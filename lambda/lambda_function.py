# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.

#Para o DynamoDB: https://developer.amazon.com/en-US/docs/alexa/hosted-skills/alexa-hosted-skills-session-persistence.html
import os
import boto3

import logging
import ask_sdk_core.utils as ask_utils
from carteira import Carteira

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_model import Response

#Definindo o dynamoDB (região, nome da tabela e adaptador de persistência)
ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')
ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)

#para coleta de logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        banco = {}
        banco = handler_input.attributes_manager.persistent_attributes
        handler_input.attributes_manager.session_attributes = handler_input.attributes_manager.persistent_attributes
        
        if not banco:
            banco['id'] = 'minhacarteira.skill@gmail.com'
            banco['saldo'] = 0
            
        speak_output = "Olá, esta é sua carteira. Você deseja listar os serviços disponíveis?"
        
        handler_input.attributes_manager.persistent_attributes = banco
        
        handler_input.attributes_manager.save_persistent_attributes()
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class ServicosIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ServicosIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Os serviços disponíveis são: incluir gasto, incluir receita, consultar saldo, consultar gastos por categoria e consultar margem para a parcela. Qual destes serviços você deseja?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

    
class ConsultaSaldoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ConsultaSaldoIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes
        '''
        session_attr['state'] = "STARTED"
        session_attr["counter"] += 1
        handler_input.attributes_manager.persistent_attributes = session_attr
        handler_input.attributes_manager.save_persistent_attributes()
        '''
        #v_saldo = session_attr['saldo', 'valor_saldo',]
        meu_saldo = ddb_table_name.get_item(
            key={
                'id': 'leonardoseivald@gmail.com'
            }
        )
        item = meu_saldo['saldo']
        #speak_output = ("Hi there, Hello World! Your saved counter is {}.",item)        
        speak_output = ("Hi there, Hello World! Your saved counter is doze.")
        #speak_output = ("Hi there, Hello World! Your saved counter is ")
        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

class IncluirGastoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("IncluirGastoIntent")(handler_input)
    
    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        if not attr:
            attr['counter'] = 13
            attr['state'] = 'ENDED'

        handler_input.attributes_manager.session_attributes = attr

        handler_input.attributes_manager.save_persistent_attributes()
        speak_output = ("Bem vindo novamente. Seu contador salvo é {}. You can say Hello or Help?".format(attr["counter"]))
        reprompt = "Say hello or help to start."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )    
        
    
class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


#sb = SkillBuilder()
sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

#sb.skill_id = "amzn.ask.skill.1"

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ServicosIntentHandler())
sb.add_request_handler(ConsultaSaldoIntentHandler())
#sb.add_request_handler(IncluirReceitaIntentHandler())
#sb.add_request_handler(ConsultaMargemIntentHandler())
sb.add_request_handler(IncluirGastoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()