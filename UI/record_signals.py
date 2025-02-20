import asyncio
import logging
import os
import cv2
import dotenv
import pickle
from g3pylib import connect_to_glasses
import time
import asyncio
from asyncio import get_running_loop
from time import sleep as time_sleep
from pylsl import StreamInlet, resolve_stream
import pathlib
import threading
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)

G3_HOSTNAME='tg03b-080202040971'

configs={
    'save_dir': os.path.join(pathlib.Path(__file__).parent.resolve(), 'recordings'),
    'sr_eeg':500,
    'print_every':1,
    'verbose':True
}

#@dataclass(slots=True)
class Recorder():
    def __init__(self, configs):
        self.configs = configs
        self.stop_event = threading.Event()
        self.first_eeg_sample_event = threading.Event() #first sample
        self.first_gaze_sample_event = threading.Event() #first sample
        self.create_folder('recordings')

    def create_folder(self,folder):
        path = self.configs['save_dir']
        if not os.path.exists(path):
            os.makedirs(folder)

    def log(self, *args):
        if self.configs['verbose']:
            logging.info(*args)


    async def record_gaze(self):
        timestamps=[]
        gaze_time= []
        file_dir = os.path.join(self.configs['save_dir'], 'gaze_data.p')
        file = open(file_dir,'wb')
        time_dir = os.path.join(self.configs['save_dir'], 'gaze_time_data.p')
        time_file = open(time_dir,'wb')
        self.log('HERE')
        async with connect_to_glasses.with_hostname(
            os.environ["G3_HOSTNAME"], using_zeroconf=True
        ) as g3:
            async with g3.stream_rtsp(gaze=True) as streams:
                async with streams.gaze.decode() as gaze_stream:
                    time_start = time.time()
                    # print(f"Gaze start time: {time_start:.6f} seconds")
                    gaze_timestamp = None
                    first_sample_time = None
                    while not self.stop_event.is_set():
                        
                        gaze, gaze_timestamp = await gaze_stream.get()
                        while gaze_timestamp is None:
                            if gaze_timestamp is None:
                                gaze, gaze_timestamp = await gaze_stream.get()

                        if not self.first_gaze_sample_event.is_set(): #first sample
                            first_sample_time = time.time()
                            logging.info(f"First gaze sample received at {first_sample_time:.6f} seconds")
                            self.first_gaze_sample_event.set()
                        self.log(f"Gaze timestamp: {gaze_timestamp}")
                        

                        # If given gaze data
                        if "gaze2d" in gaze:
                            timestamps.append({'gaze_ts':gaze_timestamp, 'gaze2d':gaze['gaze2d']})
                            # self.save_var({'gaze_ts':gaze_timestamp, 'gaze2d':gaze['gaze2d']}, file)

                    current_time = time.time()
                    gaze_time.append({'start_time':time_start, 'first_sample_time': first_sample_time, 'end_time':current_time, 'running_time':(current_time-time_start), 'gaze_ts': gaze_timestamp})
                    # print(f"Gaze end time: {time_end:.6f} seconds")
                    self.log(f'Running time: {current_time-time_start}')

        self.save_var(gaze_time,time_file)
        self.save_var(timestamps, file)
        file.close()

    async def read_single_eeg(self, inlet):
        # r = await self.loop.run_in_executor(None, inlet.sample, None)
        await asyncio.sleep(0)
        r = inlet.pull_sample()
        return r

    async def record_eeg(self):
        file_dir = os.path.join(self.configs['save_dir'], 'eeg_data.p')
        file = open(file_dir, 'wb+')
        time_dir = os.path.join(self.configs['save_dir'], 'eeg_time_data.p')
        time_file = open(time_dir,'wb')
        self.log("looking for an EEG stream...")
        streams = resolve_stream('type', 'EEG')
        sr = self.configs['sr_eeg']
        # create a new inlet to read from the stream
        inlet = StreamInlet(streams[0])
        ctr=0
        timestamps=[]
        eeg_time=[]
        time_start = time.time()
        # print(f"EEG start time: {time_start:.6f} seconds")
        eeg_timestamp = None
        first_sample_time = None
        while not self.stop_event.is_set():
            # get a new sample (you can also omit the timestamp part if you're not
            # interested in it)
            # sample, timestamp = inlet.pull_sample()
            sample, eeg_timestamp = await self.read_single_eeg(inlet)
            if not self.first_eeg_sample_event.is_set(): #first sample
                first_sample_time = time.time()
                logging.info(f"First eeg sample received at {first_sample_time:.6f} seconds")
                self.first_eeg_sample_event.set()
            # sample, timestamp = await self.read_single_eeg(inlet)
            # sample, timestamps = await self.loop.run_in_executor(None, inlet.pull_sample)
            timestamps.append({"eeg_ts": eeg_timestamp, "sample": sample}) 
            # self.log(f'Freq {ctr//sr}')
            if ctr%(self.configs['print_every']* sr)==0 and (ctr//sr)>0:
                self.log(f'EEG: {eeg_timestamp}, {sample}')
                self.log(f'Event: {self.stop_event}')
                # break
            ctr+=1
        time_end = time.time()
        eeg_time.append({'start_time':time_start, 'first_sample_time': first_sample_time, 'end_time':time_end, 'running_time':(time_end-time_start), 'eeg_ts': eeg_timestamp})
        # print(f"EEG end time: {time_end:.6f} seconds")
        self.log(f'Running time: {time_end-time_start}')
        self.save_var(timestamps, file)
        self.save_var(eeg_time,time_file)
            

    @staticmethod
    def save_var(var, file,format="pickle"):
        if format=="pickle":
            pickle.dump(var, file)

    async def test_stop_recording(self):
        #testing
        await asyncio.sleep(9)
        #end testing
        self.stop_event.set()

    def stop_recording(self):
        self.stop

    def start_recording(self):
        pass
    
    async def main(self):
        #asyncio.run(access_recordings())
        # await asyncio.gather(asyncio.to_thread(self.record_eeg()), asyncio.to_thread(self.record_gaze()), asyncio.to_thread(self.stop_recording()))
        self.loop = asyncio.get_event_loop()
        events = [self.record_eeg(), self.record_gaze()]
        await asyncio.gather(*events)
        # self.loop.run_until_complete(asyncio.gather(*events))


    def run(self):
        dotenv.load_dotenv()
        asyncio.run(self.main())

if __name__== '__main__':
    rec = Recorder(configs)
    rec.run()

    



