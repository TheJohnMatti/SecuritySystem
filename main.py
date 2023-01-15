import RPi.GPIO as GPIO
import time
from signal import signal, SIGTERM, SIGHUP, pause
from rpi_lcd import LCD
import smtplib

SERVO_PIN = 11
SERVO_OFFSET = 0.5
SERVO_MIN_ANGLE = 2.5 + SERVO_OFFSET
SERVO_MAX_ANGLE = 12.5 + SERVO_OFFSET
SMTP_SERVER = 'smtp.gmail.com'  # Email Server)
SMTP_PORT = 587  # Server Port
GMAIL_USERNAME = 'raspi.server05@gmail.com'
GMAIL_PASSWORD = 'twjgdrgzwmoeqtba'

# these GPIO pins are connected to the keypad
L1 = 21
L2 = 20
L3 = 16
L4 = 26

C1 = 19
C2 = 13
C3 = 6
C4 = 5

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

# Make sure to configure the input pins to use the internal pull-down resistors

GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(SERVO_PIN, GPIO.OUT)  # Set servoPin to OUTPUT mode
GPIO.output(SERVO_PIN, GPIO.LOW)  # Make servoPin output LOW level
p = GPIO.PWM(SERVO_PIN, 50)  # set Frequece to 50Hz
p.start(0)


def unlock():
    for dc in range(0, 101, 5):
        p.ChangeDutyCycle(dc)
        time.sleep(0.1)


def lock():
    for dc in range(100, -1, -5):
        p.ChangeDutyCycle(dc)
        time.sleep(0.1)


class Emailer:
    def sendmail(self, recipient, subject, content):
        # Create Headers
        headers = ["From: " + GMAIL_USERNAME, "Subject: " + subject, "To: " + recipient,
                   "MIME-Version: 1.0", "Content-Type: text/html"]
        headers = "\r\n".join(headers)

        # Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()

        # Login to Gmail
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

        # Send Email & Exit
        session.sendmail(GMAIL_USERNAME, recipient, headers + "\r\n\r\n" + content)
        session.quit


def main():
    lcd = LCD()
    lcd.text("", 1)
    lcd.text("", 2)
    displayText = ""

    accessGranted = False
    code = ['2', 'A', '2', 'A']

    failCnt = 0

    def lcdDisplay(text, line):
        lcd.text(text, line)

    def readLine(line, characters, typed):
        colToIndex = {C1: 0, C2: 1, C3: 2, C4: 3}
        GPIO.output(line, GPIO.HIGH)

        for i, k in colToIndex.items():
            if GPIO.input(i) == 1:
                typed.append(characters[k])

        displayText = " "
        lcdDisplay(displayText.join(typed), 2)
        GPIO.output(line, GPIO.LOW)

    # map rows to buttons
    rowToButtons = {L1: ['1', '2', '3', 'A'], L2: ["4", "5", "6", "B"],
                    L3: ["7", "8", "9", "C"], L4: ["*", "0", "3", "D"]}
    while not accessGranted:
        typed = []
        lcdDisplay("Enter password", 1)

        try:
            while len(typed) < len(code):
                # call the readLine function for each row of the keypad
                for row, buttons in rowToButtons.items():
                    readLine(row, buttons, typed)
                time.sleep(0.15)
        except KeyboardInterrupt:
            print("\nApplication stopped!")

        accessGranted = typed == code

        if accessGranted:
            lcdDisplay("Access granted", 1)
            unlock()
        else:
            failCnt += 1
            if failCnt == 3:
                lcdDisplay("Access denied", 1)
                lcdDisplay("Notifying owner", 2)
                sender = Emailer()
                sendTo = "dezelita@gmail.com"
                emailSubject = "Warning!"
                emailContent = "Someone has failed to enter your house 3 times."
                sender.sendmail(sendTo, emailSubject, emailContent)
            else:
                lcdDisplay("Wrong, try again", 1)
                time.sleep(1)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)