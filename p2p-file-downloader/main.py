import asyncio
import sys
from src.main.utils.Config import Config
from src.main.utils.Logger import Logger
from src.main.utils.FileUtils import FileUtils
from src.main.download.DownloadManager import DownloadManager
from src.main.network.NetworkMonitor import NetworkMonitor
from src.main.network.BandwidthManager import BandwidthManager
from src.main.ui.GUI import GUI

async def shutdown(gui):
    gui.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

def main():
    config = Config()
    logger = Logger(
        "P2P-Downloader",
        config.get("logging.file"),
        config.get("logging.level")
    )

    try:
        FileUtils.ensure_dir(config.get("storage.download_path"))
        FileUtils.ensure_dir(config.get("storage.temp_path"))

        network_monitor = NetworkMonitor()
        bandwidth_manager = BandwidthManager(
            max_bandwidth=config.get("network.max_bandwidth")
        )

        download_manager = DownloadManager(
            k=4,
            m=2,
            chunk_size=config.get("download.chunk_size")
        )

        loop = asyncio.get_event_loop()
        gui = GUI(download_manager)

        # 处理退出信号
        try:
            loop.run_until_complete(asyncio.gather(
                network_monitor.start_monitoring(),
                download_manager.initialize(),
                gui.run()
            ))
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        finally:
            loop.run_until_complete(shutdown(gui))

        logger.info("P2P File Downloader started")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")  # 记录错误信息
        logger.exception("An exception occurred")  # 记录异常堆栈信息
        sys.exit(1)
    finally:
        logger.info("P2P File Downloader stopped")
        logger.close()

if __name__ == "__main__":
    main()