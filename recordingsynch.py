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

logging.basicConfig(level=logging.INFO)

G3_HOSTNAME='tg03b-080202040971'

def save_var(var, dir,format="pickle"):
    if format=="pickle":


async def stream_rtsp():
    file = open('gazedata.p','wb')
    async with connect_to_glasses.with_hostname(
        os.environ["G3_HOSTNAME"], using_zeroconf=True
    ) as g3:
        async with g3.stream_rtsp(scene_camera=True, gaze=True) as streams:
            async with streams.gaze.decode() as gaze_stream, streams.scene_camera.decode() as scene_stream:
                time_start = time.time()
                for i in range(75):
                    frame, frame_timestamp = await scene_stream.get()
                    gaze, gaze_timestamp = await gaze_stream.get()
                    while gaze_timestamp is None or frame_timestamp is None:
                        if frame_timestamp is None:
                            frame, frame_timestamp = await scene_stream.get()
                        if gaze_timestamp is None:
                            gaze, gaze_timestamp = await gaze_stream.get()
                    while gaze_timestamp < frame_timestamp:
                        gaze, gaze_timestamp = await gaze_stream.get()
                        while gaze_timestamp is None:
                            gaze, gaze_timestamp = await gaze_stream.get()

                    logging.info(f"Frame timestamp: {frame_timestamp}")
                    logging.info(f"Gaze timestamp: {gaze_timestamp}")
                    
                    frame = frame.to_ndarray(format="bgr24")

                    # If given gaze data
                    if "gaze2d" in gaze:
                        pickle.dump({'gaze_ts':gaze_timestamp, 'gaze2d':gaze['gaze2d']}, file)
                        gaze2d = gaze["gaze2d"]
                        #logging.info(f'Gaze keys: {gaze.keys()}')
                        logging.info(f"Gaze2d: {gaze2d[0]:9.4f},{gaze2d[1]:9.4f}")

                        # Convert rational (x,y) to pixel location (x,y)
                        h, w = frame.shape[:2]
                        fix = (int(gaze2d[0] * w), int(gaze2d[1] * h))

                        # Draw gaze
                        frame = cv2.circle(frame, fix, 10, (0, 0, 255), 3)

                    elif i % 50 == 0:
                        logging.info(
                            "No gaze data received. Have you tried putting on the glasses?"
                        )

                    cv2.imshow("Video", frame)  # type: ignore
                    cv2.waitKey(1)  # type: ignore

                time_end = time.time()
                print(time_end-time_start)

    file.close()



async def stream_gaze():
    file = open('gazedata.p','wb')
    async with connect_to_glasses.with_hostname(
        os.environ["G3_HOSTNAME"], using_zeroconf=True
    ) as g3:
        async with g3.stream_rtsp(gaze=True) as streams:
            async with streams.gaze.decode() as gaze_stream:
                time_start = time.time()
                for i in range(75):
                   
                    gaze, gaze_timestamp = await gaze_stream.get()
                    while gaze_timestamp is None:
                        if gaze_timestamp is None:
                            gaze, gaze_timestamp = await gaze_stream.get()

                    logging.info(f"Gaze timestamp: {gaze_timestamp}")
                    

                    # If given gaze data
                    if "gaze2d" in gaze:
                        pickle.dump({'gaze_ts':gaze_timestamp, 'gaze2d':gaze['gaze2d']}, file)
                        gaze2d = gaze["gaze2d"]
                        #logging.info(f'Gaze keys: {gaze.keys()}')
                        logging.info(f"Gaze2d: {gaze2d[0]:9.4f},{gaze2d[1]:9.4f}")

                time_end = time.time()
                print(time_end-time_start)

    file.close()


async def access_recordings():
    async with connect_to_glasses.with_hostname(G3_HOSTNAME) as g3:
        async with g3.recordings.keep_updated_in_context():
            logging.info(
                f"Recordings before: {list(map(lambda r: r.uuid, g3.recordings.children))}"
            )
            await g3.recorder.start()
            logging.info("Creating new recording")
            # await asyncio.sleep(3)
            await get_running_loop().run_in_executor(None, time_sleep, 3)
            await g3.recorder.stop()
            logging.info(
                f"Recordings after: {list(map(lambda r: r.uuid, g3.recordings.children))}"
            )
            creation_time = await g3.recordings[0].get_created()
            logging.info(f"Creation time of last recording in UTC: {creation_time}")

async def record_eeg():
    logging.info("looking for an EEG stream...")
    streams = resolve_stream('type', 'EEG')
    sr = 2048
    # create a new inlet to read from the stream
    inlet = StreamInlet(streams[0])
    i=sr*3
    timestamps=[]
    while True:
        # get a new sample (you can also omit the timestamp part if you're not
        # interested in it)
        sample, timestamp = inlet.pull_sample()
        timestamps.append(timestamp)
        logging.info(timestamp, sample)
        i+=1
        if i==2:
            break

async def main():
    #asyncio.run(access_recordings())
    await asyncio.gather(stream_gaze(), access_recordings())

if __name__ == "__main__":
    dotenv.load_dotenv()
    asyncio.run(main())