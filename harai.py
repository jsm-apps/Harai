import argparse

from utils.localai import LocalAI
from utils.sqlitesearch import SqliteSearch
from utils.issues import add_issue, list_issues, show_issue
from utils.notes import Notes

focus_points=[
'XSS',
'open redirect',
'csrf',
'login',
'logout',
'onMessage',
'tokens',
'secrets',
'cloud resources',
'jsonp',
'callback params',
'reflected params'
]

questions = []

def do_next_question():
    if not questions:
        print("No more questions.")
        return
        
    noterepo = Notes()

    question = questions.pop(0)
    do_question(noterepo, ai, question)

def do_question(noterepo, ai, question, investigation_objective = None):
    question_to_ask = ""
    if investigation_objective:
        question_to_ask = "Original question:\n"+question
        question_to_ask += "\n\nCurrent objective::\n"+investigation_objective
    else:
        question_to_ask = question
        
        
    current_notes = noterepo.get_notes()
    
    print(question_to_ask)
    print("-" * 80)
    question_summary = ai.investigate_with_message_and_tools(current_notes, question_to_ask, searcher.find, searcher.find_with_record_id, searcher.next)
    print("Question Summary: "+question_summary)
    print("-" * 80)
    print("\n\n")
    
    
    # generate notes
    
    notes_to_add = ai.generate_notes(question_to_ask, question_summary, current_notes)
    noterepo.add_note(notes_to_add)
    print("**** NOTES ****")
    print(notes_to_add)
    print("**** /NOTES ****")
    
    decision = ai.decide_next_step(question_to_ask, question_summary)
    print(decision)

    if decision["action"] == "WRITE_FINDING":
        print("=" * 80)
        print("GENERATING SECURITY FINDING")
        print("=" * 80)
        current_notes = noterepo.get_notes()

        issue = ai.generate_security_issue(current_notes, question_to_ask, question_summary)

        saved_issue = add_issue(issue["title"], issue["risk_rating"], issue["details"])

        print("Security issue created:")
        print("ID:    {}".format(saved_issue["id"]))
        print("Title: {}".format(saved_issue["title"]))
        print("Risk:  {}%".format(saved_issue["risk_rating"]))
        do_next_question()


    if decision["action"] == "NEXT_QUESTION":
        do_next_question()
        
    

    if decision["action"] == "CONTINUE_RESEARCH":
        do_question(noterepo, ai, question, decision["next_step"])

def main(hardb, model):
    searcher = SqliteSearch(hardb)

    log_filename = "investigation.log"

    for focus in focus_points:
        seperator = ("=" * 80)
        print("*** "+focus+"\n")

        with open(log_filename, "w") as logfile:
            ai = LocalAI(model)
            summary = ai.investigate_with_tools(focus, searcher.find, searcher.find_with_record_id, searcher.next)
            print("=" * 80)
            print(summary)
            
            logfile.write("First Summary:\n")
            logfile.write(summary + "\n")
            logfile.write(seperator + "\n\n")
            logfile.flush()

            questions = ai.generate_investigation_questions(summary)
            do_next_question()
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Review a HAR DB for security issues, using Ollama."
    )

    parser.add_argument(
        "hardb",
        help="HAR DB to review",
        default="har.db",
    )

    parser.add_argument(
        "model",
        nargs="?",
        default="qwen3.5:latest",
        help="Ollama model to use (default: qwen3.5:latest)"
    )

    args = parser.parse_args()

    main(args.hardb, args.model)
