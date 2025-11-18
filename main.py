#!/usr/bin/env python3

from resume_builder import (
    ResumeBuilder
)

from agent import *

# Small helper for providing user feedback
user_feedback = "user_feedback.txt"
def report_weakness_to_user(information: str) -> None:
    """ Report a weakness area to the user. This is an area where the job descriptions and the user's experience does not align.

    Guidelines:
    - Provide notes to the user on what the job description asks for, but what their experience lacks.
    - Add some actionable feedback for how the user could improve.
    - Keep your answer concise.
    """
    with open(user_feedback, mode='a') as file:
        file.write(information + '\n')


if __name__ == "__main__":

  
  
    with open("experience.txt", "r") as file:
        experience_data = file.read()


    # Planner-Executor Setup
    plan_storage = {"action_items": [], "current_index": 0}
    
    def add_action_item(action_item: str) -> str:
        """Add an action item to the execution plan"""
        plan_storage["action_items"].append(action_item)
        return f"Action item added: {action_item[:50]}... (Total: {len(plan_storage['action_items'])})"
    
    planner_tools = {
        "add_action_item": add_action_item,
    }
    
    # Using Planner-Executioner for high level execution of the task.
    planner_system_prompt = """You are a planning agent. Your task is to generate a relevant and competitive resume by analyzing a job description and breaking the work into actionable steps for an executor agent.

    About the Executor Agent:
    - The executor receives candidate experience data (limited to fit context window) and a specific action item you create.
    - The executor uses this data to complete the instruction and write to the resume. If data is insufficient, it will notify the user.
    - The executor has NO knowledge of the job description. You must explicitly mention relevant job requirements, skills, and keywords in each action item.
    - Be descriptive and specific about what the executor should look for in the user's data and how to phrase it.
    - The executor has no knowledge of the data collected from other task executors, in other words, each task is siloed.

    About the Resume Creation Process:
    - First: Fill out contact information (name, address, phone, email).
    - Last: Write the summary using the overlap between job requirements and user skills.
    - Order all other sections logically between these two steps.

    About Your Role:
    - You start with no user information. You may receive feedback from the executor containing user information.
    - Based on executor feedback, you may need to replan your strategy.
    - The job description may mention may general skills and experiences in 1 sentence, you are responsible for making an action item for each atomic skill and experience.
    - Before making tool calls, summarize each of the main skills and experiences and try to consolidate some that are very similar to reduce the size of the plans.

    Instructions:
    - Use the add_action_item tool to add each action item one at a time.
    - Respond with "task complete" when all action items have been added.
    - When instructing, do not use words like 'Request', 'Ask', or anything indicating that the executor must interact with the user directly.
    """
    
    planner = Agent(
        system_prompt=planner_system_prompt,
        tools=planner_tools,
        model="gpt-4o-mini",
        max_iterations=5
    )


    # Using Chain of thought reason for individual exeuction of tasks
    executor_prompt = """You are an execution agent. Your purpose is to fill out resume entries using provided experience data and tools that insert data into the resume.

    You will receive:
    - An action item from the planner describing what to add to the resume
    - Candidate experience data relevant to the action item

    Your process (use chain-of-thought reasoning):
    1. Think through the problem step-by-step:
       - Analyze what the action item is asking for (skills, experiences, qualifications, etc.)
       - Review the candidate's experience data and identify relevant information
       - Compare what's required vs. what's available
       - Summarize the candidate's data according to the action item
       - Decide if the data is sufficient to complete the task
    
    2. Based on your reasoning:
       - If sufficient: Use the appropriate tools to add entries to the resume.
       - If insufficient: Use the 'report_weakness_to_user' tool to highlight missing experience data.
    
    3. Respond with 'task_complete' after either adding entries or reporting weaknesses.

    Always show your reasoning process before making decisions about the data.

    """


    latex_resume = ResumeBuilder("test.tex")

    # we can pass class methods to the LLM if they have been bound to an object
    executor_tools = {
        "set_name": latex_resume.set_name,
        "set_address": latex_resume.set_address,
        "set_phone_number": latex_resume.set_phone_number,
        "set_email": latex_resume.set_email, 
        "add_contact": latex_resume.add_contact,
        "set_summary": latex_resume.set_summary,
        "add_skills": latex_resume.add_skills, 
        "add_work_experience": latex_resume.add_work_experience,
        "report_weakness_to_user": report_weakness_to_user
    }

    executor = Agent(
        system_prompt=executor_prompt,
        tools=executor_tools,
        model="gpt-4o-mini",
        max_iterations=10
    )

    ########## User prompt to start
    user_prompt = f"""Create a resume using this job description
    
    Job description:
    
    ```
    About the job\nAt Cadence, we hire and develop leaders and innovators who want to make an impact on the world of technology.\nCadence is the leader in hardware emulation-prototyping technology and products. System engineering team is responsible to define, validate and enable the products. We are now looking for a hands-on system integration engineer who wants to expand his/her scope, work with the interactions of a complex multi-rack system and grow his/her career.\nThis position is a highly visible function to bridge and gate-keep the full integration, validation, and characterization of ASIC, HW/PCB, SW, FW, and FPGA subsystems in the whole development cycle. The same discipline also applies to system bring-up and testing, methodology development and verification.\nKey Responsibilities\nLeverage silicon verification platform and environment to create necessary post-silicon infrastructure, methodology and automation to allow tests executed in a timely and efficient manner.\nIntegrate silicon, HW, firmware, and system software into a complete system which includes various InfiniBand and PCIe protocols, PXE booting, virtual machines, secure networks, Ethernet and Ethernet-over-Infiniband, sockets and RPC calls, FPGA, microcontroller interfaces, JTAG, I2C, SPI, SERDES, memory and many other interfaces.\nExecute post-silicon tests to expose design issues, validate product against the specifications including performance, and qualify the design for production release.\nReview, replicate, and respond to customer issues. Perform initial analysis of error logs from customer design simulation runs. Debug and isolate system-level issues down to ASIC/FPGAs, host servers, subsystems, firmware modules, runtime diagnostics.\nDevelop silicon and system stress tests. Leverage tests developed by other engineers. Package tests for production and field use.\nDefine, develop and drive the implementation of validation automation environment.\nPosition Requirements\nBS in Electrical Engineering, Computer Engineering or Computer Science\nFluent in at least one functional scripting language, preferably but not limited to Python. Other languages are plus.\nExperience with embedded software/firmware, operating systems, and/or HW/SW interfaces is a plus\nExperience in developing, maintaining and operating automated engineering processes is a big plus.\nStrong interpersonal and communication skills, self-motivated and ability to work with cross-functions teams around the globe.\nThe annual salary range for California is $88,900 to $165,100. You may also be eligible to receive incentive compensation: bonus, equity, and benefits. Sales positions generally offer a competitive On Target Earnings (OTE) incentive compensation structure. Please note that the salary range is a guideline and compensation may vary based on factors such as qualifications, skill level, competencies and work location. Our benefits programs include: paid vacation and paid holidays, 401(k) plan with employer match, employee stock purchase plan, a variety of medical, dental and vision plan options, and more.\nWe\u2019re doing work that matters. Help us solve what others can\u2019t.\n\u2026 more\nBenefits found in job post\n401(k)
    ```
    
    """

    # Planner creates plan
    planner_result = planner.run(user_prompt)
    
    for p in plan_storage['action_items']:

        print(f"- {p}")
    # Execute action items one at a time
    while plan_storage["current_index"] < len(plan_storage["action_items"]):
        action_item = plan_storage["action_items"][plan_storage["current_index"]]
        executor_prompt = f"Given this exeperience data from the user:\n{experience_data}\n\nExecute this action item, following the guidelines provided:\n{action_item}\n\n"
        executor_result = executor.run(executor_prompt)
        
        # Capture executor's full context from conversation history when task is complete
        executor_context = ""
        if executor.conversation_history:
            for msg in executor.conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if content:
                    executor_context += f"[{role}]: {content}\n"
                # Include tool calls and results
                if msg.get("tool_calls"):
                    executor_context += f"[tool_calls]: {msg.get('tool_calls')}\n"
        
        # # Feed back to planner with executor's context
        # if executor_context:
        #     planner.run(f"Executor completed action {plan_storage['current_index'] + 1}:\n{executor_context}\n\nContinue with next action or replan if needed.")
        
        plan_storage["current_index"] += 1
        executor.conversation_history = []  # Reset executor context for next action item

        latex_resume.save()