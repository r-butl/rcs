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
    
    planner_system_prompt = """You are a planning agent, where the task is to use a job description and a user's experience data to generate a relevant and competive resume. Break down the task into actionable steps than an executor agent will carry out. 

    Things to know about the Executor Agent:
    - the agent will be provided with experience data of the candidate (a small enough amount to fit into the context window) and the specifc action item that you have described for it to carry out.
    - the executor agent will use that data to complete the instruction and write it to the resume. if the there is insufficient data present, then the executor will write a note to the user explaining that they were unable to find good information for the job.
    - The executor will need to know what specifically to look for in the user's data regarding the job description. You will need to be descriptive in your assignments so that the executor knows explicitly what to look for or how to phrase things.
    - The executor agent has no knowledge of the job description, so referring to it is not helpful. Explicitly mention the items in the job description that are relevant to the task
    
    Things to know about the Resume Creation process:
    - Instruct the executor agent to first fill out the contact information for the user.
    - The final instruction should be writing the summary, using the overlap of the most relevant parts of the job description and user skills.

    Things to know about your Role:
    - You will not be provided any user information from the start. You may recieve feedback from the Executor that contains user information. 
    - Given the feedback from the Executor Agent, you may need to replan your strategy for filling out the resume.
    

    Use the add_action_item tool to add each action item one at a time. Use "task complete" when all action items have been added."""
    
    planner = Agent(
        system_prompt=planner_system_prompt,
        tools=planner_tools,
        model="gpt-4o-mini",
        max_iterations=5
    )


    executor_prompt = """You are an execution agent whose sole purpose is to fill out resume entries provided some data and a set of tools that insert the data into the resume. You will be given an action item and experience data from the user. Your instructions are as follows:

    1. Determine if the data provided is adequate enough to fulfill the task.
    2. If yes, use the tools provided to add entries to the resume.
    3. If no, use the 'report_weakness_to_user' tool to highlight the missing experience data.
    4. Use the phrase 'task_complete' when you have either added entries fulfilling the task, or have reported weaknesses to the user.

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
    
    print(plan_storage)
    # # Execute action items one at a time
    # while plan_storage["current_index"] < len(plan_storage["action_items"]):
    #     action_item = plan_storage["action_items"][plan_storage["current_index"]]
    #     executor_prompt = f"Execute this action item:\n{action_item}\n\nExperience data:\n{experience_data}"
    #     executor_result = executor.run(executor_prompt)
        
    #     # Capture executor's full context from conversation history when task is complete
    #     executor_context = ""
    #     if executor.conversation_history:
    #         for msg in executor.conversation_history:
    #             role = msg.get("role", "")
    #             content = msg.get("content", "")
    #             if content:
    #                 executor_context += f"[{role}]: {content}\n"
    #             # Include tool calls and results
    #             if msg.get("tool_calls"):
    #                 executor_context += f"[tool_calls]: {msg.get('tool_calls')}\n"
        
    #     # Feed back to planner with executor's context
    #     if executor_context:
    #         planner.run(f"Executor completed action {plan_storage['current_index'] + 1}:\n{executor_context}\n\nContinue with next action or replan if needed.")
        
    #     plan_storage["current_index"] += 1
    #     executor.conversation_history = []  # Reset executor context for next action item

    # latex_resume.save()