from crazymocap.utils import radio_tx_init

class RadioStreamer:
    def __init__(self, channel, data_rate, mode):
        self.radio=radio_tx_init(channel=channel, data_rate=data_rate, mode=mode)

    def connect_to_motive(self):
        pass

    def check_radio_connection(self):
        pass

    def start_stream(self):
        pass

    def stop_stream(self):
        pass