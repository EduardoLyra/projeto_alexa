# -*- coding: utf-8 -*-

#                   ChangeLog
# => Implementada função de reconhecimento de dia desejado. 20-09-2021
# => Implementada leitura de json. 22-09-2021
#
#                   To Do
# => REFATORAR O CÓDIGO
#       -> criar funções para a criação de token
#       -> melhorar o desempenho dos requests(importar a biblioteca httpx e asyncio);
# => Implementar sitema de respostas;

import logging
import requests
from pytz import timezone
import datetime
import json

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractRequestInterceptor, AbstractExceptionHandler)
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.skill_builder import SkillBuilder, CustomSkillBuilder
from ask_sdk_model.services.reminder_management import (
    Trigger, TriggerType, AlertInfo, AlertInfoSpokenInfo, SpokenText, PushNotification, PushNotificationStatus, ReminderRequest, Recurrence, RecurrenceFreq)

from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor
from ask_sdk_model.services.service_exception import ServiceException
from ask_sdk_model.interfaces.connections import SendRequestDirective

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from get_Tokens import Token
from logica import Time


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PERMISSIONS = ["alexa::alerts:reminders:skill:readwrite"]
TIME_ZONE_ID = 'America/Sao_Paulo'

ERROR = "Uh Oh. Parece que algo deu errado"
NOTIFY_MISSING_PERMISSIONS = "Habilite as permissões de lembrete no aplicativo Amazon Alexa para prosseguir."


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Bem vindo a sua Agenda Geo Care, em que posso te ajudar?"
        speak_reprompt = "Eu posso te informar sobre o seu próximo compromisso ou sua agenda completa de hoje, o que você está precisando?"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_reprompt)
            .response
        )


class AgendaIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AgendaIntent")(handler_input)

    def handle(self, handler_input):
        t = Token()
        userTimeZone = t.time_zone(handler_input)
        if userTimeZone == "ERROR":
            handler_input.response_builder.speak(
                "Houve um problema ao conectar com o serviço")
            return handler_input.response_builder.response

        data = datetime.datetime.now(timezone(userTimeZone))
        ano, mes, dia, hora, minuto = data.year, data.month, data.day, data.hour, data.minute

        with open("horarios.json") as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()
        rotina = ''
        prox = handler_input.request_envelope.request.intent.slots['proximo'].value
        slots = handler_input.request_envelope.request.intent.slots['tempo'].value
        if prox == 'próximo':
            for item in jsonObject['rotina']:
                h = Time()
                atividade, hora_item = h.verifica_proximo(item, hora, minuto)
            speak_output = "A sua próxima atividade é {atividade} às {hora_item}.".format(
                atividade=atividade, hora_item=hora_item)
        else:
            ano_desejado, mes_desejado, dia_desejado = slots.split("-")
            difDia = int(dia_desejado) - dia

            for item in jsonObject['rotina']:
                rotina += 'às ' + item['hora'] + ' ' + item['atividade'] + '. '
            if difDia == 0:
                speak_output = "A sua rotina de hoje é {rotina}".format(
                    rotina=rotina)
            elif difDia == 1:
                speak_output = "A sua rotina de amanhã é {rotina}".format(
                    rotina=rotina)
            elif difDia == -1:
                speak_output = "A sua rotina de ontem foi {rotina}".format(
                    rotina=rotina)
            else:
                dia_final = dia + difDia
                speak_output = "A sua rotida do dia {dia_final} é {rotina}".format(
                    dia_final=dia_final, rotina=rotina)
        return (
            handler_input.response_builder
            .speak(speak_output)
            .response
        )


class CriarLembreteIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("IntentRequest")(handler_input) and is_intent_name("CriarLembreteIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("Lembrete Intent Handler")
        requests_envelope = handler_input.request_envelope
        response_builder = handler_input.response_builder
        reminder_service = handler_input.service_client_factory.get_reminder_management_service()

        t = Token()
        t.reminder(handler_input)
        userTimeZone = t.time_zone(handler_input)

        if userTimeZone == "ERROR":
            handler_input.response_builder.speak(
                "Houve um problema ao conectar com o serviço")
            return handler_input.response_builder.response

        if not(requests_envelope.context.system.user.permissions and requests_envelope.context.system.user.permissions.consent_token):

            return response_builder.add_directive(
                SendRequestDirective(
                    name="AskFor",
                    payload={
                        "@type": "AskForPermissionsConsentRequest",
                        "@version": "1",
                        "permissionScope": "alexa::alerts:reminders:skill:readwrite"
                    },
                    token="correlationToken"
                )
            ).response
        with open("horarios.json") as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()

        agora = datetime.datetime.now(timezone(userTimeZone))

        for item in jsonObject['rotina']:
            h = Time()
            horario = h.verifica_hora(item, agora)
            notification_time = horario.strftime("%Y-%m-%dT%H:%M:%S")
            trigger = Trigger(object_type=TriggerType.SCHEDULED_ABSOLUTE, scheduled_time=notification_time,
                              time_zone_id=TIME_ZONE_ID)
            text = SpokenText(
                locale='pt-BR', ssml="<speak>Ótimo! Criei um lembrete para você.</speak>", text="{}".format(item['atividade']))
            alert_info = AlertInfo(AlertInfoSpokenInfo([text]))
            push_notification = PushNotification(
                PushNotificationStatus.ENABLED)
            reminder_request = ReminderRequest(
                notification_time, trigger, alert_info, push_notification)
            try:
                reminder_response = reminder_service.create_reminder(
                    reminder_request)
                logger.info("Lembrete Criado: {}".format(reminder_response))
            except ServiceException as e:
                logger.info("Exceção encontrada: {}".format(e.body))
                return response_builder.speak(ERROR).response
        return response_builder.speak("Pronto! Seus lembretes foram criados com sucesso! Te avisarei no horário de cada um de seus cuidados.").set_card(SimpleCard("Lembrete geo care", "Lembretes de todos seus cuidados de hoje foram criados")).response


class ConnectionsResponseHandler(AbstractRequestHandler):
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput) -> bool
        return ((is_request_type("Connections.Response")(handler_input) and
                handler_input.request_envelope.request.name == "AskFor"))

    def handle(self, handler_input, exception):
        # type: (HandlerInput) -> Response
        logger.info("Em Conecctions Response Handler")

        response_payload = handler_input.resquest_envelope.resquest.payload
        response_status = response_payload['status']

        logger.info("Status value is --> {}".format(response_status))

        if (response_status == 'NOT_ANSWERED'):
            return handler_input.response_builder.speak(
                "Forneça permissão de lembrete usando o cartão que enviei para seu aplicativo Alexa.").set_card(AskForPermissionsConsentCard(permissions=PERMISSIONS)).response
        elif (response_status == 'DENIED'):
            return handler_input.response_builder.speak(
                "Você pode fornecer permissão a qualquer momento pelo aplicativo da Alexa").response
        else:
            return handler_input.response_builder.speak(
                "Você quer marcar o horario?").ask("Oque quer fazer?").response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Eu posso te informar sobre o seu próximo compromisso ou sua agenda completa de hoje, o que você está precisando?"

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
        speak_output = "Até a próxima!"

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
        speech = "Hmm, não tenho certeza. Você pode dizer Olá ou Ajuda. O que você gostaria de fazer?"
        reprompt = "Eu não entendi isso. Com o que posso ajudar?"

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
        speak_output = "Você acabou de ativar " + intent_name + "."

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

        speak_output = "Desculpe, tive problemas para fazer o que você pediu. Por favor, tente novamente."

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """ Log the request envelope. """

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("Request Received : {}".format(
            handler_input.request_envelope))


class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """ Log the response envelope """

    def process(self, handler_input, response):
        # type: (HandlerInput) -> None
        logger.info("Response generated: {}".format(response))


sb = CustomSkillBuilder(api_client=DefaultApiClient())

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(AgendaIntentHandler())
sb.add_request_handler(CriarLembreteIntentHandler())
sb.add_request_handler(ConnectionsResponseHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(LoggingRequestInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()
