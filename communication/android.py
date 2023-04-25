import json
import os
import socket
from typing import Optional
import bluetooth
from communication.link import Link


class AndroidMessage:
    """
    Class for communicating with Android tablet over Bluetooth connection.
    """

    def __init__(self, cat: str, value: str):
        """
        Constructor for AndroidMessage.
        :param cat: Message category.
        :param value: Message value.
        """
        self._cat = cat
        self._value = value

    @property
    def cat(self):
        """
        Returns the message category.
        :return: String representation of the message category.
        """
        return self._cat

    @property
    def value(self):
        """
        Returns the message as a string.
        :return: String representation of the message.
        """
        return self._value

    @property
    def jsonify(self) -> str:
        """
        Returns the message as a JSON string.
        :return: JSON string representation of the message.
        """
        return json.dumps({'cat': self._cat, 'value': self._value})


class AndroidLink(Link):
    """Class for communicating with Android tablet over Bluetooth connection. 

    ## General Format
    Messages between the Android app and Raspi will be in the following format:
    ```json
    {"cat": "xxx", "value": "xxx"}
    ```

    The `cat` (for category) field with the following possible values:
    - `info`: general messages
    - `error`: error messages, usually in response of an invalid action
    - `location`: the current location of the robot (in Path mode)
    - `image-rec`: image recognition results
    - `mode`: the current mode of the robot (`manual` or `path`)
    - `status`: status updates of the robot (`running` or `finished`)
    - `obstacle`: list of obstacles 

    ## Android to RPi

    #### Set Obstacles
    The contents of `obstacles` together with the configured turning radius (`settings.py`) will be passed to the Algorithm API.
    ```json
    {
    "cat": "obstacles",
    "value": {
        "obstacles": [{"x": 5, "y": 10, "id": 1, "d": 2}],
        "mode": "0"
    }
    }
    ```
    RPi will store the received commands and path and make a call to the Algorithm API

    ### Start
    Signals to the robot to start dispatching the commands (when obstacles were set).
    ```json
    {"cat": "control", "value": "start"}
    ```

    If there are no commands in the queue, the RPi will respond with an error:
    ```json
    {"cat": "error", "value": "Command queue is empty, did you set obstacles?"}
    ```

    ### Image Recognition 

    #### RPi to Android
    ```json
    {"cat": "image-rec", "value": {"image_id": "A", "obstacle_id":  "1"}}
    ```

    ### Location Updates (RPi to Android)
    In Path mode, the robot will periodically notify Android with the updated location of the robot.
    ```json
    {"cat": "location", "value": {"x": 1, "y": 1, "d": 0}}
    ```
    where `x`, `y` is the location of the robot, and `d` is its direction.



    """

    def __init__(self):
        """
        Initialize the Bluetooth connection.
        """
        super().__init__()
        self.client_sock = None
        self.server_sock = None

    def connect(self):
        """
        Connect to Andriod by Bluetooth
        """
        self.logger.info("Bluetooth connection started")
        try:
            # Set RPi to be discoverable in order for service to be advertisable
            os.system("sudo hciconfig hci0 piscan")

            # Initialize server socket
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind(("", bluetooth.PORT_ANY))
            self.server_sock.listen(1)

            # Parameters
            port = self.server_sock.getsockname()[1]
            uuid = '94f39d29-7d6d-437d-973b-fba39e49d4ee'

            # Advertise
            bluetooth.advertise_service(self.server_sock, "MDP-Group2-RPi", service_id=uuid, service_classes=[
                                        uuid, bluetooth.SERIAL_PORT_CLASS], profiles=[bluetooth.SERIAL_PORT_PROFILE])

            self.logger.info(
                f"Awaiting Bluetooth connection on RFCOMM CHANNEL {port}")
            self.client_sock, client_info = self.server_sock.accept()
            self.logger.info(f"Accepted connection from: {client_info}")

        except Exception as e:
            self.logger.error(f"Error in Bluetooth link connection: {e}")
            self.server_sock.close()
            self.client_sock.close()

    def disconnect(self):
        """Disconnect from Android Bluetooth connection and shutdown all the sockets established"""
        try:
            self.logger.debug("Disconnecting Bluetooth link")
            self.server_sock.shutdown(socket.SHUT_RDWR)
            self.client_sock.shutdown(socket.SHUT_RDWR)
            self.client_sock.close()
            self.server_sock.close()
            self.client_sock = None
            self.server_sock = None
            self.logger.info("Disconnected Bluetooth link")
        except Exception as e:
            self.logger.error(f"Failed to disconnect Bluetooth link: {e}")

    def send(self, message: AndroidMessage):
        """Send message to Android"""
        try:
            self.client_sock.send(f"{message.jsonify}\n".encode("utf-8"))
            self.logger.debug(f"Sent to Android: {message.jsonify}")
        except OSError as e:
            self.logger.error(f"Error sending message to Android: {e}")
            raise e

    def recv(self) -> Optional[str]:
        """Receive message from Android"""
        try:
            tmp = self.client_sock.recv(1024)
            self.logger.debug(tmp)
            message = tmp.strip().decode("utf-8")
            self.logger.debug(f"Received from Android: {message}")
            return message
        except OSError as e:  # connection broken, try to reconnect
            self.logger.error(f"Error receiving message from Android: {e}")
            raise e
