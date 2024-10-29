import requests
import urllib

user_id = None  # TELEGRAM
token = None  # TELEGRAM


def SendMessage(message, log=True):
    if not user_id or not token:
        return

    try:
        encoded_message = urllib.parse.quote_plus(message)

        # Construct the URL
        send_text = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={user_id}&parse_mode=Markdown&text={encoded_message}"

        send_text = (
            "https://api.telegram.org/bot"
            + token
            + "/sendMessage?chat_id="
            + user_id
            + "&parse_mode=Markdown&text="
            + message
        )
        res = requests.get(send_text)
        if res.ok:
            return res.json()
        else:
            print(res.json())
            print("Telegram failure")

    except Exception:
        print("send message failed")
