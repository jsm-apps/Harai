import argparse

from utils.localai import LocalAI
from utils.sqlitesearch import SqliteSearch
from utils.issues import add_issue, list_issues, show_issue
from utils.notes import Notes

class Harai():
    def __init__(self, hardb, model, minsteps, maxsteps):
        self.hardb = hardb
        self.model = model
        self.searcher = SqliteSearch(self.hardb)
        self.min_steps = minsteps
        self.max_steps = maxsteps

        self.focus_points = [
            "Search functionality: identify search inputs, parameters, endpoints, reflected search terms, returned HTML, and client-side handling that would be useful for manual XSS testing.",

            "Cross-site scripting (XSS): identify user-controlled inputs, reflected values, HTML or JavaScript contexts, DOM manipulation, and client-side data flows that would provide useful targets for manual XSS testing.",

            "Open redirects: identify parameters, endpoints, authentication flows, and response behaviour that control redirect destinations or navigation targets.",

            "Cross-site request forgery (CSRF): identify state-changing requests, their HTTP methods, authentication mechanisms, cookies, request parameters, and observable anti-CSRF controls.",

            "Login functionality: identify login endpoints, authentication requests, credentials and parameters, tokens, cookies, redirects, error responses, and related authentication flows.",

            "Logout functionality: identify logout endpoints, HTTP methods, session or token behaviour, redirects, and requests involved in ending an authenticated session.",

            "Cross-window messaging: identify JavaScript using postMessage or message event handlers, message data processing, origin handling, and functionality influenced by received messages.",

            "Tokens: identify authentication, session, API, access, refresh, reset, verification, and other security-relevant tokens together with where they are transmitted or returned.",

            "Secrets and sensitive values: identify credentials, API keys, secret values, private configuration, connection information, and other sensitive data exposed within captured requests or responses.",

            "Cloud resources: identify cloud service endpoints, storage resources, object URLs, cloud hostnames, resource identifiers, configuration, and references to cloud infrastructure.",

            "JSONP: identify JavaScript or API responses using callback-based JSON delivery and parameters that influence the callback function name.",

            "Callback parameters: identify parameters associated with callbacks, return destinations, redirect destinations, continuation URLs, and other application-controlled navigation or callback behaviour.",

            "Reflected input: identify request parameters or other user-controlled values that appear in corresponding responses, preserving the parameter, endpoint, response context, and record ID where available."
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

        decision= {}
        if step_counter < self.min_steps:
            decision = ai.generate_next_step(question_to_ask, question_summary)
        else:
            decision = ai.decide_next_step(question_to_ask, question_summary)
        

        # we may decide to write a finding, so force next question only if action returned is continue research when we have reached max steps
        if step_counter >= self.max_steps and decision["action"] == "CONTINUE_RESEARCH":
            print("Max steps reached, moving onto next question...")
            decision["action"] = "NEXT_QUESTION"

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

    parser.add_argument(
        "--min-steps",
        type=int,
        default=3,
        help="Minimum investigation steps (default: 3)"
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum investigation steps (default: 10)"
    )

    args = parser.parse_args()

    app = Harai(args.hardb, args.model, args.min_steps, args.max_steps)
    app.main()
