import json
import ollama
from utils.promptutil import PromptUtil
from utils.ollamautil import OllamaUtil

pu = PromptUtil()
global_notes = pu.load_from_file("prompts/global_notes.txt")
search_fields_info = pu.load_from_file("prompts/search_fields_info.txt")
scope = pu.load_from_file("inscope.txt")


class LocalAI():
    def __init__(self, model):
        self.model = model
        self.ollamautil = OllamaUtil(self.model)

    def investigate_with_tools(self, focusarea, search_function, search_withid_function, next_function):
        functions = {
            search_function.__name__: search_function,
            search_withid_function.__name__: search_withid_function,
            next_function.__name__: next_function
        }
        
        pu = PromptUtil()
        system_prompt = pu.load_from_file(
            "prompts/investigate_with_tools/investigate_with_tools.system.txt", 
            search_fields_info=search_fields_info, 
            global_notes=global_notes,
            scope=scope
        )
        user_prompt = pu.load_from_file(
            "prompts/investigate_with_tools/investigate_with_tools.user.txt", 
            focusarea=focusarea
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        max_tool_calls = 10
        tool_call_count = 0

        while tool_call_count < max_tool_calls:
            print("Thinking...")
            response = None
            
            while response is None:
                try:

                    response = ollama.chat(
                        model=self.model,
                        messages=messages,
                        tools=[
                            search_function,
                            next_function
                        ],
                        think=False
                    )
                except Exception as e:
                    print("Error: {}".format(e))
                    print("Retrying...")

            message = response["message"]
            messages.append(message)

            tool_calls = message.get("tool_calls", [])

            # If the model tries to stop early, tell it to continue.
            if not tool_calls:
                print("Continue investigating...")
                messages.append({
                    "role": "user",
                    "content": (
                        "Continue investigating. "
                        "Use one of the available tools and do not provide "
                        "the final summary yet."
                    )
                })
                continue

            for tool_call in tool_calls:

                if tool_call_count >= max_tool_calls:
                    break

                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"].get("arguments", {})

                if function_name not in functions:
                    print("Error: Unknown function: " + function_name)
                    result = {
                        "error": "Unknown function: " + function_name
                    }

                else:
                    try:
                        print("Tool call: {}({})".format(function_name, arguments))
                        result = functions[function_name](**arguments)
                        print(result)

                    except Exception as e:
                        result = {
                            "error": str(e)
                        }

                tool_call_count += 1

                messages.append({
                    "role": "tool",
                    "tool_name": function_name,
                    "content": json.dumps(result)
                })

        # Investigation complete.
        # No tools are supplied on this call, so the model must summarise.
        user_prompt = pu.load_from_file(
            "prompts/investigate_with_tools/investigate_with_tools_summary.user.txt"
        )
        
        messages.append({"role": "user", "content": user_prompt})
        
        return self.ollamautil.chat_with_text_response(messages)

    def investigate_with_message_and_tools(self, current_notes, message, search_function, search_withid_function, next_function):
        functions = {
            search_function.__name__: search_function,
            search_withid_function.__name__: search_withid_function,
            next_function.__name__: next_function
        }
        
        pu = PromptUtil()
        system_prompt = pu.load_from_file(
            "prompts/investigate_with_message_and_tools/investigate_with_message_and_tools.system.txt", 
            search_fields_info=search_fields_info, 
            global_notes=global_notes,
            scope=scope
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        max_tool_calls = 10
        tool_call_count = 0

        while tool_call_count < max_tool_calls:
            print("Thinking...")
            
            response = None
            
            while response is None:
                try:
                    response = ollama.chat(
                        model=self.model,
                        messages=messages,
                        tools=[
                            search_function,
                            next_function
                        ],
                        think=False
                    )
                    
                except Exception as e:
                    print("Error: {}".format(e))
                    print("Retrying...")

            ai_message = response["message"]
            messages.append(ai_message)

            tool_calls = ai_message.get("tool_calls", [])

            if not tool_calls:
                print("Continue investigating...")

                messages.append({
                    "role": "user",
                    "content": (
                        "Continue investigating based on my original request. "
                        "Use one of the available tools and do not provide "
                        "the final summary yet."
                    )
                })

                continue

            for tool_call in tool_calls:
                if tool_call_count >= max_tool_calls:
                    break

                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"].get("arguments", {})

                if function_name not in functions:
                    print("Error: Unknown function: " + function_name)

                    result = {
                        "error": "Unknown function: " + function_name
                    }

                else:
                    try:
                        print("=" * 80)
                        print("Tool call: {}({})".format(
                            function_name,
                            arguments
                        ))

                        result = functions[function_name](**arguments)

                    except Exception as e:
                        result = {
                            "error": str(e)
                        }

                tool_call_count += 1

                messages.append({
                    "role": "tool",
                    "tool_name": function_name,
                    "content": json.dumps(result)
                })
                
        user_prompt = pu.load_from_file(
            "prompts/investigate_with_message_and_tools/investigate_with_message_and_tools_summary.user.txt", 
            message=message, 
            current_notes=current_notes
        )

        messages.append({"role": "user", "content": user_prompt})

        return self.ollamautil.chat_with_text_response(messages)


    def generate_investigation_questions(self, summary):
        pu = PromptUtil()
        system_prompt = pu.load_from_file(
            "prompts/generate_investigation_questions/generate_investigation_questions.system.txt", 
            global_notes=global_notes
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": summary}
        ]
        
        while True:
            try:
                response = ollama.chat(model=self.model, messages=messages, format="json", think=False)
                content = response["message"]["content"]
                data = json.loads(content)
                return data["questions"]
            except json.JSONDecodeError as e:
                print("Invalid JSON returned by AI: {}".format(e))
                print("Retrying...")

    def decide_next_step(self, question, summary):
        pu = PromptUtil()
        system_prompt = pu.load_from_file(
            "prompts/decide_next_step/decide_next_step.system.txt", 
            global_notes=global_notes
        )
        user_prompt = pu.load_from_file(
            "prompts/decide_next_step/decide_next_step.user.txt", 
            question=question,
            summary=summary
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        while True:
            try:
                response = ollama.chat(model=self.model, messages=messages, format="json", think=False)
                jsoncontent = json.loads(response["message"]["content"])
                return jsoncontent
            except json.JSONDecodeError as e:
                print("Invalid JSON returned by AI: {}".format(e))
                print("Retrying...")




    def generate_security_issue(self, current_notes, question, summary):       
        pu = PromptUtil()
        system_prompt = pu.load_from_file(
            "prompts/generate_security_issue/generate_security_issue.system.txt"
        )
        user_prompt = pu.load_from_file(
            "prompts/generate_security_issue/generate_security_issue.user.txt",
            question=question,
            summary=summary,
            current_notes=current_notes
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        validjson = False
        issue = None
        while(validjson == False):
            try:
                response = ollama.chat(model=self.model, messages=messages, format="json", think=False)
                issue = json.loads(response["message"]["content"])
                validjson=True
            except json.JSONDecodeError as e:
                print("Invalid JSON returned by AI: {}".format(e))
                print("Retrying...")

        # Validate required fields
        if "title" not in issue:
            raise ValueError("AI issue is missing title")

        if "risk_rating" not in issue:
            raise ValueError("AI issue is missing risk_rating")

        if "details" not in issue:
            raise ValueError("AI issue is missing details")

        # Validate risk
        issue["risk_rating"] = int(
            issue["risk_rating"]
        )

        if issue["risk_rating"] < 0 or issue["risk_rating"] > 100:
            raise ValueError(
                "AI returned invalid risk_rating"
            )

        return issue
        
    def generate_notes(self, question_to_ask, question_summary, current_notes):
        pu = PromptUtil()
        system_prompt = pu.load_from_file(
            "prompts/generate_notes/generate_notes.system.txt"
        )
        user_prompt = pu.load_from_file(
            "prompts/generate_notes/generate_notes.user.txt",
            question_to_ask=question_to_ask,
            question_summary=question_summary,
            current_notes=current_notes
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.ollamautil.chat_with_text_response(messages)
        
