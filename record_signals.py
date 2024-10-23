import asyncio
import logging
import os
import cv2
import dotenv
import pickle
from g3pylib import connect_to_glasses
import time
from asyncio import get_running_loop
from time import sleep as time_sleep
from pylsl import StreamInlet, resolve_stream
import pathlib
import threading

logging.basicConfig(level=logging.INFO)

G3_HOSTNAME='tg03b-080202040971'

configs={
    'save_dir': os.path.join(pathlib.Path(__file__).parent.resolve(), 'recordings'),
    'sr_eeg':512,
    'print_every':1,
    'verbose':True
}

@dataclass(slots=True)
class Recorder():
    configs: dict

    def __post_init__(self):
        self.stop_event = threading.Event()
        self.create_folder('recordings')

    def create_folder(self,folder):
        if not os.path.exists(os.path.join(self.configs['save_dir'], folder)):
            os.makedirs(folder)

    def log(self, *args):
        if self.configs['verbose']:
            logging.info(*args)


    async def stream_gaze(self):
        file_dir = os.path.join(self.configs['save_dir'], 'recordings', 'gaze_data.p')
        file = open(file_dir,'wb')
        async with connect_to_glasses.with_hostname(
            os.environ["G3_HOSTNAME"], using_zeroconf=True
        ) as g3:
            async with g3.stream_rtsp(gaze=True) as streams:
                async with streams.gaze.decode() as gaze_stream:
                    time_start = time.time()
                    while not self.stop_event.is_set():
                    
                        gaze, gaze_timestamp = await gaze_stream.get()
                        while gaze_timestamp is None:
                            if gaze_timestamp is None:
                                gaze, gaze_timestamp = await gaze_stream.get()

                        self.log(f"Gaze timestamp: {gaze_timestamp}")
                        

                        # If given gaze data
                        if "gaze2d" in gaze:
                            self.save_var({'gaze_ts':gaze_timestamp, 'gaze2d':gaze['gaze2d']}, file)

                    time_end = time.time()
                    self.log(f'Running time: {time_end-time_start}')

        file.close()

    async def record_eeg(self):
        file_dir = os.path.join(self.configs['save_dir'], 'recordings', 'eeg_data.p')
        file = open(file_dir, 'wb')
        self.log("looking for an EEG stream...")
        streams = resolve_stream('type', 'EEG')
        sr = self.configs['sr_eeg']
        # create a new inlet to read from the stream
        inlet = StreamInlet(streams[0])
        ctr=0
        timestamps=[]
        while not self.stop_event.is_set():
            # get a new sample (you can also omit the timestamp part if you're not
            # interested in it)
            sample, timestamp = inlet.pull_sample()
            timestamps.append(timestamp)

            if (ctr//sr)%self.configs['print_every']==0 and (ctr//sr)>0:
                self.log(timestamp, sample)
            ctr+=1

    @staticmethod
    def save_var(var, file,format="pickle"):
        if format=="pickle":
            pickle.dump(var, file)

    def stop_recording(self):
        #testing
        time.sleep(5)
        #end testing
        self.stop_event.set()

    def start_recording():
        pass
    
    async def main():
        #asyncio.run(access_recordings())
        await asyncio.gather(stream_gaze(), access_recordings())

    def run():
        dotenv.load_dotenv()
        asyncio.run(main())

if __name__== '__main__':
    rec = Recorder(configs)
    rec.run()

    



