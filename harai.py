import argparse

from utils.localai import LocalAI
from utils.sqlitesearch import SqliteSearch
from utils.issues import add_issue, list_issues, show_issue
from utils.notes import Notes

class Harai():
    def __init__(self, hardb, model):
        self.hardb = hardb
        self.model = model
        self.searcher = SqliteSearch(self.hardb)
        self.min_steps = 10

        self.focus_points=[
            'XSS within search functionality',
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

        self.questions = []

    def do_next_question(self, ai):
        if not self.questions:
            print("No more questions.")
            return
            
        noterepo = Notes()

        question = self.questions.pop(0)
        self.do_question(0, noterepo, ai, question)

    def do_question(self, step_counter, noterepo, ai, question, investigation_objective = None):
        question_to_ask = ""
        if investigation_objective:
            question_to_ask = "Original question:\n"+question
            question_to_ask += "\n\nCurrent objective::\n"+investigation_objective
        else:
            question_to_ask = question
            
            
        current_notes = noterepo.get_notes()
        
        print(question_to_ask)
        print("-" * 80)
        question_summary = ai.investigate_with_message_and_tools(
            current_notes, 
            question_to_ask, 
            self.searcher.find, 
            self.searcher.find_with_record_id, 
            self.searcher.next
        )
        print("Question Summary: "+question_summary)
        print("-" * 80)
        print("\n\n")
        
        
        # generate notes
        
        notes_to_add = ai.generate_notes(question_to_ask, question_summary, current_notes)
        noterepo.add_note(notes_to_add)
        print("**** NOTES ****")
        print(notes_to_add)
        print("**** /NOTES ****\n\n")

        step_counter = step_counter + 1

        decision= ""
        if step_counter < self.min_steps:
            decision = ai.generate_next_step(question_to_ask, question_summary)
        else:
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
            self.do_next_question(ai)


        if decision["action"] == "NEXT_QUESTION":
            self.do_next_question(ai)
            
        

        if decision["action"] == "CONTINUE_RESEARCH":
            self.do_question(step_counter, noterepo, ai, question, decision["next_step"])

    def main(self):
        log_filename = "investigation.log"

        for focus in self.focus_points:
            seperator = ("=" * 80)
            print("*** "+focus+"\n")

            with open(log_filename, "w") as logfile:
                ai = LocalAI(self.model)
                summary = ai.investigate_with_tools(
                    focus, 
                    self.searcher.find, 
                    self.searcher.find_with_record_id, 
                    self.searcher.next
                )
                print("=" * 80)
                print(summary)
                
                logfile.write("First Summary:\n")
                logfile.write(summary + "\n")
                logfile.write(seperator + "\n\n")
                logfile.flush()

                self.questions = ai.generate_investigation_questions(summary)
                print("\nQUESTIONS\n")
                print(self.questions)
                print("\n\n")
                self.do_next_question(ai)
        
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

    app = Harai(args.hardb, args.model)
    app.main()
