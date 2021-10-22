import datetime


class Time:
    def verifica_hora(self, item, agora):
        if item['hora'][1] != ':':
            horario = agora.replace(
                hour=int(self.item['hora'][0] + item['hora'][1]),
                minute=int(item['hora'][3] + item['hora'][4]),
                second=0)
            horario += datetime.timedelta(days=+1)
            return horario
        else:
            horario = agora.replace(
                hour=int(item['hora'][0]),
                minute=int(item['hora'][2] + item['hora'][3]),
                second=0)
            horario += datetime.timedelta(days=+1)
            return horario

    def verifica_proximo(self, item, hora, minuto):
        if item['hora'][1] != ':':
            hora_json = int(item['hora'][0] + item['hora'][1])
            min_json = int(item['hora'][3] + item['hora'][4])
            if hora_json > hora:
                atividade = item['atividade']
                horaItem = item['hora']
                return atividade, horaItem

            elif hora_json == hora and min_json > minuto:
                atividade = item['atividade']
                horaItem = item['hora']
                return atividade, horaItem

        else:
            hora_json = int(item['hora'][0])
            min_json = int(item['hora'][2] + item['hora'][3])
            if hora_json > hora:
                atividade = item['atividade']
                horaItem = item['hora']
                return atividade, horaItem

            elif hora_json == hora and min_json > minuto:
                atividade = item['atividade']
                horaItem = item['hora']
                return atividade, horaItem
