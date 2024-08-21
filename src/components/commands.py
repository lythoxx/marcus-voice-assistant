import sys
from enum import Enum
import requests

from dateutil import parser
from pytube import YouTube
from ytmusicapi import YTMusic

from config.config import Config

from src import utils

from .speech import Speech
from .tts import TTS


class Commands(Enum):
    HELP = ("help",)
    EXIT = ("exit",)
    TEST = ("test",)
    ALARM = ("alarm", "wake")
    STOP = ("stop",)
    PLAY_MUSIC = ("play",)
    WEATHER = ("weather", "forecast", "temperature")

    def get_command(keywords: list, entities: list, all_keywords: list):
        for keyword in all_keywords:
            print(keyword)
            match keyword.lower():
                # case "setup":
                #     print("Found setup")
                #     return Commands.SETUP
                # case "set up":
                #     print("Found set up")
                #     return Commands.SETUP
                case "help":
                    print("Found help")
                    return Commands.HELP
                case "exit":
                    print("Found exit")
                    return Commands.EXIT
                case "test":
                    print("Found test")
                    return Commands.TEST
                case "alarm" | "wake":
                    print("Found alarm")
                    if "stop" in all_keywords:
                        return Commands.STOP
                    return Commands.ALARM
                case "stop":
                    print("Found stop")
                    return Commands.STOP
                case "play":
                    print("Found play")
                    return Commands.PLAY_MUSIC
                case "weather" | "forecast" | "temperature":
                    print("Found weather")
                    return Commands.WEATHER
        else:
            return None

    def run_command(command, times=None, music_query=None) -> bool:
        match command:
            # case Commands.SETUP:
            #     return Commands.setup()
            case Commands.HELP:
                return Commands.help()
            case Commands.EXIT:
                return Commands.exit()
            case Commands.TEST:
                return Commands.test()
            case Commands.ALARM:
                return Commands.alarm(times)
            case Commands.PLAY_MUSIC:
                return Commands.play_music(music_query)
            case Commands.WEATHER:
                return Commands.weather()
            case _:
                return False


    def help() -> bool:
        return True

    def exit():
        tts = TTS()
        tts.speak_openai("Auf wiedersehen! Ich hoffe ich war hilfreich.")
        sys.exit(0)

    def test() -> bool:
        tts = TTS()
        tts.speak_openai("Das ist ein Testbefehl")
        tts.speak_openai("Test erfolgreich")
        return True

    def alarm(times) -> bool:
        print(times)
        tts = TTS()
        if len(times) == 0:
            tts.speak_openai("Es scheint als hättest du keine Zeit für den Wecker angegeben.")
            tts.speak_openai("Bitte gebe eine Zeit an, um den Wecker zu starten.")
            return False
        time = times[0]
        if len(times) > 1:
            tts.speak_openai("Es scheint als hättest du mehrere Zeiten für den Wecker angegeben.")
            tts.speak_openai("Ich werde die erste, genannte Zeit für den Wecker verwenden.")
        try:
            alarm_time = parser.parse(time)
        except ValueError:
            tts.speak_openai("Es scheint als die Zeit ungültig. Ich kann keinen Wecker mit der gegebenen Zeit stellen.")
            return False

        print(alarm_time.strftime("%H:%M"))
        tts.speak_openai("Ist der Wecker wiederholend?")
        speech = Speech()
        answer = speech.recognize()
        if answer:
            if "no" in answer.lower():
                Config.set_alarm(alarm_time.strftime("%H:%M"))
                tts.speak_openai("Ich habe den Wecker auf " + alarm_time.strftime("%H") + "Uhr" + alarm_time.strftime("%M") + " gesetzt.")
            elif "yes" in answer.lower():
                tts.speak_openai("An welchen Tagen soll der Wecker wiederholt werden?")
                answer = speech.recognize()
                if not answer:
                    tts.speak_openai("Es scheint als hättest du keine gültige Antwort gegeben. Ich habe den Wecker auf " + alarm_time.strftime("%H") + "Uhr" + alarm_time.strftime("%M") + " gesetzt.")
                    return True
                days = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]
                alarm_days = ""
                for word in answer.lower():
                    if word in days:
                        alarm_days += word + ","
                Config.set_alarm(alarm_time.strftime("%H:%M"), alarm_days)
                tts.speak_openai("Ich habe den Wecker auf " + alarm_time.strftime("%H") + "Uhr" + alarm_time.strftime("%M") + " gesetzt. Der Wecker wird {alarm_days} wiederholt.")
        else:
            Config.set_alarm(alarm_time.strftime("%H:%M"))
            tts.speak_openai("Ich habe den Wecker auf " + alarm_time.strftime("%H") + "Uhr" + alarm_time.strftime("%M") + " gesetzt.")
        return True

    def play_music(query: str, stop_music_event, filter=None) -> bool:
        ytmusic = YTMusic()
        tts = TTS()
        if "album" in query.lower():
            filter = "albums"
        elif "song" in query.lower() or "lied" in query.lower() or "track" in query.lower():
            filter = "songs"

        if filter is None:
            search_results = ytmusic.search(query)
        else:
            print("Filter: " + filter)
            search_results = ytmusic.search(query, filter=filter)

        if not search_results:
            print("No results found.")
            return False

        # Get the first result
        first_result = search_results[0]

        # Get the type of the first result
        result_type = first_result['resultType']

        # Handle the result based on its type
        if result_type == 'song':
            # Get the audio track URL
            audio_url = first_result['videoId']

            # Use pytube to download and play the audio
            yt = YouTube(f"https://www.youtube.com/watch?v={audio_url}")
            stream = yt.streams.filter(only_audio=True).first()
            stream.download(output_path='output', filename=f'{first_result['title']}.mp3')

            # Play the audio
            # tts.speak_openai(f"Jetzt spiele ich {first_result['title']} von {first_result['artists'][0]['name']}.")
            utils.play_mp3(f'output/{first_result["title"]}.mp3', stop_music_event)

        elif result_type == 'album':
            # Get the album's track list
            album_id = first_result['browseId']
            album = ytmusic.get_album(album_id)
            # Play each song in the album
            tts.speak_openai(f"Hier ist das Album {album['title']} von {album['artists'][0]['name']}.")
            for track in album['tracks']:
                Commands.play_music(f"{track['title']} {album['artists'][0]['name']}", stop_music_event, filter="songs")

        # elif result_type == 'artist':
        #     # Get the artist's top songs
        #     artist_id = first_result['artists'][0]['id']
        #     artist = ytmusic.get_artist(artist_id)

        #     # Play each top song
        #     print(artist['songs'])
        #     for track in artist['songs']:
        #         play_music(f"{track['title']} {artist['name']}")
        elif result_type == "video":
            search_results = ytmusic.search(query, filter="songs")

            if not search_results:
                print("No results found.")
                return False

            # Get the first result
            first_result = search_results[0]

            # Get the type of the first result
            result_type = first_result['resultType']
            print(f"Result type: {result_type}")
                    # Get the audio track URL
            audio_url = first_result['videoId']

            # Use pytube to download and play the audio
            yt = YouTube(f"https://www.youtube.com/watch?v={audio_url}")
            stream = yt.streams.filter(only_audio=True).first()
            stream.download(output_path='output', filename=f'{first_result['title']}.mp3')

            # Play the audio
            utils.play_mp3(f'output/{first_result["title"]}.mp3', stop_music_event)

        else:
            print(f"Unsupported result type: {result_type}")
            return False

        return True

    def weather():
        api_key = Config.get_config("config")["weather_key"]
    # latitude and longitude for Berlin, Germany
        lat = "52.5200"
        lon = "13.4050"
        url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}&units=metric&lang=de"

        response = requests.get(url)

        print(response.status_code)

        if response.status_code == 200:
            data = response.json()
            temperature = data['current']['temp']
            description_id = data['current']['weather'][0]['id']
            description_main = data['current']['weather'][0]['main']
            description = utils.get_weather_descriptions(description_id, description_main)
            probability_precipitation = data['daily'][0]['pop']
            tts = TTS()
            tts.speak_openai(f"Die aktuelle Temperatur beträgt {int(temperature)} Grad Celsius, bei {description}. Die Tiefsttemperatur ist {int(data['daily'][0]['temp']['min'])} Grad Celsius, und die Höchsttemperatur {int(data['daily'][0]['temp']['max'])} Grad Celsius. Die Regenwahrscheinlichkeit beträgt {int(probability_precipitation)}%.")
            return True
        else:
            tts.speak_openai("Ich konnte leider keine Wetterdaten finden. Bitte versuche es später erneut.")
            return False
