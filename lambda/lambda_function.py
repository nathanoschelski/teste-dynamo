# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.

#Para o DynamoDB: https://developer.amazon.com/en-US/docs/alexa/hosted-skills/alexa-hosted-skills-session-persistence.html
import os
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr


import logging
import ask_sdk_core.utils as ask_utils
from carteira import Carteira

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from decimal import Decimal
from datetime import datetime

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_model import Response

#Definindo o dynamoDB (região, nome da tabela e adaptador de persistência)
ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')
ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)
ddb_client = boto3.client('dynamodb')
tabela = ddb_resource.Table(ddb_table_name)

#para coleta de logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

lista_servicos = "Os serviços disponíveis são: incluir gasto, incluir receita, consultar saldo ou remover a última operação. O quê você quer?"

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)
        
    ##
    ##

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speak_output = "Olá, esta é sua carteira. Você pode incluir gasto, incluir receita, consultar saldo ou remover a última operação. O quê você quer?"
        #speak_output = "Olá, esta é sua carteira."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

## Funções inicio
def atualiza_saldo(valor,tipo_operacao):
    if tipo_operacao == 'receita':
        novo_saldo = saldo_atual() + valor
    else:
        if tipo_operacao == 'gasto':
            novo_saldo = saldo_atual() - valor
    tabela.update_item(
        Key={
            'id': 'saldo'
        },
        UpdateExpression="set valor=:r",
        ExpressionAttributeValues={
            ':r': novo_saldo
        },            
    )

#Função de consulta do saldo no DynamoDB    
def saldo_atual():
    try:
        meu_saldo = tabela.get_item(Key={'id': 'saldo'},ProjectionExpression='valor')['Item']['valor']
        response = meu_saldo

    except ClientError as e:
        response = '0'
    return response

def contador_operacoes(operador):
    #se for adicionar uma nova operação é passado o parâmetro 'add' então o contador de operações é incremnentado, se for uma remoção o parâmetro 'remove' diminui a quantidade de operações
    if operador == 'add':
        contador = tabela.get_item(Key={'id': 'saldo'},ProjectionExpression='qtdade_operacoes')['Item']['qtdade_operacoes'] + 1
    else:
        if operador == 'remove':
            contador = tabela.get_item(Key={'id': 'saldo'},ProjectionExpression='qtdade_operacoes')['Item']['qtdade_operacoes'] - 1
    tabela.update_item(
        Key={
            'id': 'saldo'
        },
        UpdateExpression="set qtdade_operacoes=:r",
        ExpressionAttributeValues={
            ':r': contador
        },            
    )
    return 'op' + str(contador)

def texto_para_decimal(reais, centavos):
    
    if reais is not None and centavos is not None:
        valor_receibo = Decimal(reais) + (Decimal(centavos)/100)
    else:
        if reais is None:
            valor_receibo = (Decimal(centavos)/100)
        else:
            if centavos is None:
                valor_receibo = Decimal(reais)
            else:
                valor_receibo = 0 
    return valor_receibo

def saldo_para_texto():
    # type: (HandlerInput) -> Response

    saldo = saldo_atual()

    reais = str(saldo // 1)
    centavos = str(int((saldo % 1) * 100))
    speak_output = "Você não tem saldo."
    if int(reais) > 0 and int(centavos) > 0:
        speak_output = reais + " reais e " + centavos + " centavos"
    else:
        if int(reais) > 0 and int(centavos) <= 0:
            speak_output = reais + " reais"
        else:
            if int(reais) <= 0 and int(centavos) > 0:
                speak_output = centavos + " centavos"
    return  speak_output

def remover_operacao():
    qtdade = tabela.get_item(Key={'id': 'saldo'},ProjectionExpression='qtdade_operacoes')['Item']['qtdade_operacoes']
    id_a_remover = 'op' + str(qtdade)
    item_a_remover = tabela.get_item(Key={'id': id_a_remover})
    valor_item_removido = (item_a_remover)['Item']['valor']
    tipo_item_removido = str((item_a_remover)['Item']['tipo'])
    atualiza_saldo(valor_item_removido,tipo_item_removido)
    qtdade_operacoes = contador_operacoes('remove')
    tabela.delete_item(
        Key={
            'id': id_a_remover
        }
    )  

## Funções final

class ServicosIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ServicosIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = lista_servicos

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

#inteção teste

class EutenhoIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("EutenhoIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #result = tabela.get_item(Key={'categoria': 'comida'},ProjectionExpression='valor')['Item']['valor']
        '''
        table = ddb_resource.Table(ddb_table_name)
        response = table.query(
            TableName=ddb_table_name,
            KeyConditionExpression='categoria= :catego',
            ExpressionAttributeValues={
                ':catego': {'S': 'comida'}
            }

            
        )
        '''
        #criar_index()
        '''
        response = tabela.scan(FilterExpression=Attr('categoria').eq('comida'))
        data = response['Items']
        '''
        #speak_output = "Você acionou a função teste." + str(response['Items'])
        speak_output = "teste aqui ok."
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
        speak_output = "Seu saldo atual é " + saldo_para_texto()

        #speak_output = "Olá, esta é sua carteira. Seu saldo atual é? mil reais"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Deseja algo mais?")
                .response
        )

class IncluirGastoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("IncluirGastoIntent")(handler_input)
    
    def handle(self, handler_input):

        reais = handler_input.request_envelope.request.intent.slots['reais'].value
        centavos = handler_input.request_envelope.request.intent.slots['centavos'].value        
        
        valor_gasto = texto_para_decimal(reais,centavos)

        categoria = str(handler_input.request_envelope.request.intent.slots['categoria_gasto'].value)
        
        if valor_gasto <= saldo_atual():
            atualiza_saldo(valor_gasto,'gasto')
            qtdade_operacoes = contador_operacoes('add')

            try:
                speak_output = "Registrado o gasto no valor de: " + str(valor_gasto) + " reais na categoria: " + categoria + ". Seu saldo agora é " + saldo_para_texto()
                tabela = ddb_resource.Table(ddb_table_name)
                tabela.put_item(
                    Item={
                        "id": qtdade_operacoes,
                        "valor": valor_gasto,
                        "tipo": "gasto",
                        "categoria": categoria,
                        "dia" : datetime.today().strftime('%d'),
                        "mes" : datetime.today().strftime('%m'),
                        "ano" : datetime.today().strftime('%Y')
                    }
                )

            except ValueError:
                speak_output = "Houve um erro ao salvar o gasto."    

        else:
            speak_output = "Você não tem saldo suficiente para este gasto. Seu saldo atual é " + saldo_para_texto()


        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Deseja algo mais?")
                .response
        )    


## Terminar função
class RemoverOperacaoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("RemoverOperacaoIntent")(handler_input)
    
    def handle(self, handler_input):

        #após o usuário confirmar que realmente deseja excluir a última operação, a ação é executada
        confirma = str(handler_input.request_envelope.request.intent.confirmation_status.value)
        if confirma == 'CONFIRMED':
            remover_operacao()
            
            speak_output = "Última operação foi removida com sucesso."


        else:
            speak_output = "Remoção cancelada!"

        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Deseja algo mais?")
                .response
        )
    
class IncluirReceitaIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("IncluirReceitaIntent")(handler_input)
    
    def handle(self, handler_input):

        #valor_ganho = int(handler_input.request_envelope.request.intent.slots['valor_ganho'].value)
        reais = handler_input.request_envelope.request.intent.slots['reais'].value
        centavos = handler_input.request_envelope.request.intent.slots['centavos'].value        
        
        valor_ganho = texto_para_decimal(reais,centavos)
        atualiza_saldo(valor_ganho,'receita')
        qtdade_operacoes = contador_operacoes('add')
        speak_output = "Registrada receita no valor de: " + str(valor_ganho) + " reais. Seu saldo agora é " + saldo_para_texto()           
        
        tabela = ddb_resource.Table(ddb_table_name)
        tabela.put_item(
            Item={
                "id": qtdade_operacoes,
                "valor": valor_ganho,
                "tipo": "receita",
                "dia" : datetime.today().strftime('%d'),
                "mes" : datetime.today().strftime('%m'),
                "ano" : datetime.today().strftime('%Y')                
            }
        )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Deseja algo mais?")
                .response
        )    


class HelpIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = lista_servicos

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
        speak_output = "O primeiro passo é gastar menos do que você ganha. Até mais."

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
        speech = "Hmm, não entendi seu comando." + lista_servicos
        reprompt = "Não entendi seu pedido, o quê você quer?"

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

        speak_output = "Desculpe, houve algum problema com sua solicitação. Favor tentar novamente."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()
sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

#sb.skill_id = "amzn.ask.skill.1"

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ServicosIntentHandler())
sb.add_request_handler(ConsultaSaldoIntentHandler())
sb.add_request_handler(IncluirReceitaIntentHandler())
#sb.add_request_handler(ConsultaMargemIntentHandler())
sb.add_request_handler(IncluirGastoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(RemoverOperacaoIntentHandler())
sb.add_request_handler(EutenhoIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers


sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()