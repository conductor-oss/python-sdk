import time
import uuid
from typing import List

from conductor.client.ai.orchestrator import AIOrchestrator
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.timeout_policy import TimeoutPolicy


def main():
    agent1_provider = 'openai_v1'
    agent1_model = 'gpt-4'

    agent1_provider = 'mistral'
    agent1_model = 'mistral-large-latest'

    agent2_provider = 'anthropic_cloud'
    agent2_model = 'claude-3-sonnet-20240229'
    # anthropic_model = 'claude-3-opus-20240229'

    moderator_provider = 'cohere_saas'
    moderator_model = 'command-r'

    mistral = 'mistral'
    mistral_model = 'mistral-large-latest'

    api_config = Configuration()

    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()

    moderator = 'moderator'
    moderator_text = """You are very good at moderating the debates and discussions. In this discussion, there are 2 panelists, ${ua1} and ${ua2}.
    As a moderator, you summarize the discussion so far, pick one of the panelist ${ua1} or ${ua2} and ask them a relevant question to continue the discussion.
        You are also an expert in formatting the results into structured json format.  You only output a valid JSON as a response.
        You answer in RFC8259 compliant 
        JSON format ONLY with two fields result and user. You can effectively manage a hot discussion while keeping it 
        quite civil and also at the same time continue the discussion forward encouraging participants and their views. 
        Your answer MUST be in a JSON dictionary with keys "result" and "user".  Before answer, check the output for correctness of the JSON format.
        The values MUST not have new lines or special characters that are not escaped.  The JSON must be RFC8259 compliant.
        
        You produce the output in the following JSON keys:

        {
         "result": ACTUAL_MESSAGE
         "user": USER_WHO_SOULD_RESPOND_NEXT --> One of ${ua1} or ${ua2}
        }

        "result" should summarize the conversation so far and add the last message in the conversation.  
        "user" should be the one who should respond next.          
        You be fair in giving chance to all participants, alternating between ${ua1} and ${ua2}.  
        the last person to talk was ${last_user} 
        Do not repeat what you have said before and do not summarize the discussion each time, 
        just use first person voice to ask questions to move discussion forward.
        Do not use filler sentences like 'in this discussion....'
        JSON:
        
        """

    agent1 = 'agent_1'
    agent1_text = """
    You are ${ua1} and you reason and think like ${ua1}.  Your language reflects your persona.
    You are very good at analysis of the content and coming up with insights and questions on the subject and the context.
    You are in a panel with other participants discussing a specific event/topic as set in the context.  
    You avoid any repetitive argument, discussion that you have already talked about.          
    Here is the context on the conversation, add a follow up with your insights and questions to the conversation:
    Do not mention that you are an AI model.
    ${context}
    
    You answer in a very clear way, do not add any preamble to the response:
    """

    agent2 = 'agent_2'
    agent2_text = """
    You are ${ua2} and you reason and think like ${ua2}.  Your language reflects your persona.
    You are very good at continuing the conversation with more insightful question.  
    You are in a panel with other participants discussing a specific event/topic as set in the context.
    You bring in your contrarian views to the conversation and always challenge the norms.  
    You avoid any repetitive argument, discussion that you have already talked about.
    Your responses are times extreme and a bit hyperbolic. 
    When given the history of conversation, you ask a meaningful followup question that continues to conversation
    and dives deeper into the topic.
    Do not mention that you are an AI model.
    Here is the context on the conversation: 
    ${context}
    
    You answer in a very clear way, do not add any preamble to the response:
    """

    orchestrator = AIOrchestrator(api_configuration=api_config)

    orchestrator.add_prompt_template(moderator, moderator_text, 'moderator instructions')
    orchestrator.associate_prompt_template(moderator, moderator_provider, [moderator_model])

    orchestrator.add_prompt_template(agent1, agent1_text, 'agent1 instructions')
    orchestrator.associate_prompt_template(agent1, agent1_provider, [agent1_model])

    orchestrator.add_prompt_template(agent2, agent2_text, 'agent2 instructions')
    orchestrator.associate_prompt_template(agent2, agent2_provider, [agent2_model])

    get_context = SimpleTask(task_reference_name='get_document', task_def_name='GET_DOCUMENT')
    get_context.input_parameter('url','${workflow.input.url}')

    wf_input = {'ua1': 'donald trump', 'ua2': 'joe biden', 'last_user': '${workflow.variables.last_user}',
                'url': 'https://www.foxnews.com/media/billionaire-mark-cuban-dodges-question-asking-pays-fair-share-taxes-pay-owe'}

    template_vars = {
        'context': get_context.output('result'),
        'ua1': '${workflow.input.ua1}',
        'ua2': '${workflow.input.ua2}',
    }

    max_tokens = 500
    moderator_task = LlmChatComplete(task_ref_name='moderator_ref',
                                     max_tokens=2000,
                                     llm_provider=moderator_provider, model=moderator_model,
                                     instructions_template=moderator,
                                     messages='${workflow.variables.history}',
                                     template_variables={
                                         'ua1': '${workflow.input.ua1}',
                                         'ua2': '${workflow.input.ua2}',
                                         'last_user': '${workflow.variables.last_user}'
                                     })

    agent1_task = LlmChatComplete(task_ref_name='agent1_ref',
                                  max_tokens=max_tokens,
                                  llm_provider=agent1_provider, model=agent1_model,
                                  instructions_template=agent1,
                                  messages=[ChatMessage(role='user', message=moderator_task.output('result'))],
                                  template_variables=template_vars)

    set_variable1 = (SetVariableTask(task_ref_name='task_ref_name1')
                     .input_parameter('history',
                                      [
                                          ChatMessage(role='assistant', message=moderator_task.output('result')),
                                          ChatMessage(role='user',
                                                      message='[' + '${workflow.input.ua1}] ' + f'{agent1_task.output("result")}')
                                       ])
                     .input_parameter('_merge', True)
                     .input_parameter('last_user', "${workflow.input.ua1}"))

    agent2_task = LlmChatComplete(task_ref_name='agent2_ref',
                                  max_tokens=max_tokens,
                                  llm_provider=agent2_provider, model=agent2_model,
                                  instructions_template=agent2,
                                  messages=[ChatMessage(role='user', message=moderator_task.output('result'))],
                                  template_variables=template_vars)

    set_variable2 = (SetVariableTask(task_ref_name='task_ref_name2')
                     .input_parameter('history', [
        ChatMessage(role='assistant', message=moderator_task.output('result')),
        ChatMessage(role='user', message='[' + '${workflow.input.ua2}] ' + f'{agent2_task.output("result")}')
    ])
                     .input_parameter('_merge', True)
                     .input_parameter('last_user', "${workflow.input.ua2}"))

    init = SetVariableTask(task_ref_name='init_ref')
    init.input_parameter('history',
                         [ChatMessage(role='user',
                                      message="""analyze the following context:
                                      BEGIN
                                      ${get_document.output.result}
                                      END """)]
                         )
    init.input_parameter('last_user', '')

    wf = ConductorWorkflow(name='multiparty_chat_tmp', version=1, executor=workflow_executor)

    script = """
    (function(){         
        if ($.user == $.ua1) return 'ua1';
        if ($.user == $.ua2) return 'ua2';
        return 'ua1';
    })();
    """
    next_up = SwitchTask(task_ref_name='next_up_ref', case_expression=script, use_javascript=True)
    next_up.switch_case('ua1', [agent1_task, set_variable1])
    next_up.switch_case('ua2', [agent2_task, set_variable2])
    next_up.input_parameter('user', moderator_task.output('user'))
    next_up.input_parameter('ua1', '${workflow.input.ua1}')
    next_up.input_parameter('ua2', '${workflow.input.ua2}')

    loop_tasks = [moderator_task, next_up]
    chat_loop = LoopTask(task_ref_name='loop', iterations=6, tasks=loop_tasks)
    wf >> get_context >> init >> chat_loop



    wf.timeout_seconds(1200).timeout_policy(timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW)
    wf.register(overwrite=True)

    result = wf.execute(wait_until_task_ref=agent1_task.task_reference_name, wait_for_seconds=1,
                        workflow_input=wf_input)

    result = workflow_client.get_workflow_status(result.workflow_id, include_output=True, include_variables=True)
    print(f'started workflow {api_config.ui_host}/{result.workflow_id}')
    while result.is_running():
        time.sleep(10)  # wait for 10 seconds LLMs are slow!
        result = workflow_client.get_workflow_status(result.workflow_id, include_output=True, include_variables=True)
        op = result.variables['history']
        if len(op) > 1:
            print('=======================================')
            print(f'{op[len(op) - 1]["message"]}')
            print('\n')


if __name__ == '__main__':
    main()
