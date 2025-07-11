# main.py - EchoWatch Emergency Monitor
import time
import threading
import logging
import signal
import sys
from datetime import datetime

from src.config import ensure_directories, LOGS_DIR
from src.broadcastify_monitor import BroadcastifyMonitor
from src.audio_processor import AudioProcessor
from src.llm_analyzer import LLMAnalyzer
from src.file_manager import FileManager

# Set up main logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EchoWatch:
    def __init__(self):
        self.running = False
        self.broadcastify_monitor = None
        self.audio_processor = AudioProcessor()
        self.llm_analyzer = LLMAnalyzer()
        self.file_manager = FileManager()
        
        # Threading events
        self.stop_event = threading.Event()
        self.threads = []
        
        # Statistics
        self.start_time = time.time()
        self.stats = {
            'files_downloaded': 0,
            'files_processed': 0,
            'batches_analyzed': 0,
            'alerts_sent': 0
        }
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("🛑 Shutdown signal received")
        self.stop()
    
    def start(self):
        """Start all EchoWatch components"""
        logger.info("🎵 Starting EchoWatch Emergency Monitor")
        logger.info("=" * 60)
        
        # Ensure directories exist
        ensure_directories()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        
        # Start Broadcastify monitoring in separate thread
        logger.info("🌐 Starting Broadcastify monitor...")
        broadcastify_thread = threading.Thread(
            target=self.run_broadcastify_monitor,
            name="BroadcastifyMonitor"
        )
        broadcastify_thread.daemon = True
        broadcastify_thread.start()
        self.threads.append(broadcastify_thread)
        
        # Start audio processing in separate thread
        logger.info("🎤 Starting audio processor...")
        audio_thread = threading.Thread(
            target=self.run_audio_processor,
            name="AudioProcessor"
        )
        audio_thread.daemon = True
        audio_thread.start()
        self.threads.append(audio_thread)
        
        # Start LLM analysis in separate thread
        logger.info("🤖 Starting LLM analyzer...")
        llm_thread = threading.Thread(
            target=self.run_llm_analyzer,
            name="LLMAnalyzer"
        )
        llm_thread.daemon = True
        llm_thread.start()
        self.threads.append(llm_thread)
        
        # Start statistics reporting
        stats_thread = threading.Thread(
            target=self.run_stats_reporter,
            name="StatsReporter"
        )
        stats_thread.daemon = True
        stats_thread.start()
        self.threads.append(stats_thread)
        
        logger.info("✅ All components started successfully")
        
        # Main thread waits for shutdown
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
        finally:
            self.stop()
    
    def run_broadcastify_monitor(self):
        """Run Broadcastify monitoring in a thread"""
        try:
            self.broadcastify_monitor = BroadcastifyMonitor()
            
            if not self.broadcastify_monitor.setup_driver():
                logger.error("Failed to initialize Broadcastify monitor")
                return
            
            logger.info("📡 Broadcastify monitor initialized")
            
            while self.running and not self.stop_event.is_set():
                try:
                    # Monitor for new calls
                    new_calls = self.broadcastify_monitor.monitor_network_traffic(duration_seconds=30)
                    
                    if new_calls:
                        self.stats['files_downloaded'] += len(new_calls)
                        logger.info(f"📥 Downloaded {len(new_calls)} new calls")
                    
                    if self.stop_event.wait(timeout=5):  # Check stop event every 5 seconds
                        break
                        
                except Exception as e:
                    logger.error(f"Error in Broadcastify monitor: {e}")
                    if self.stop_event.wait(timeout=10):  # Wait before retry
                        break
                        
        except Exception as e:
            logger.error(f"Fatal error in Broadcastify monitor: {e}")
        finally:
            if self.broadcastify_monitor:
                self.broadcastify_monitor.stop()
    
    def run_audio_processor(self):
        """Run audio processing in a thread"""
        try:
            logger.info("🎤 Audio processor initialized")
            
            while self.running and not self.stop_event.is_set():
                try:
                    # Process any new inbound files
                    processed_count = self.audio_processor.process_all_inbound_files()
                    
                    if processed_count > 0:
                        self.stats['files_processed'] += processed_count
                        logger.info(f"✅ Processed {processed_count} audio files")
                    
                    # Wait before next check
                    if self.stop_event.wait(timeout=10):  # Check every 10 seconds
                        break
                        
                except Exception as e:
                    logger.error(f"Error in audio processor: {e}")
                    if self.stop_event.wait(timeout=15):  # Wait before retry
                        break
                        
        except Exception as e:
            logger.error(f"Fatal error in audio processor: {e}")
    
    def run_llm_analyzer(self):
        """Run LLM analysis in a thread"""
        try:
            logger.info("🤖 LLM analyzer initialized")
            
            while self.running and not self.stop_event.is_set():
                try:
                    # Check if ready to process a batch
                    analysis = self.llm_analyzer.process_batch_if_ready()
                    
                    if analysis:
                        self.stats['batches_analyzed'] += 1
                        
                        # Check for alerts
                        severity = analysis.get('overall_severity', 0)
                        if severity >= self.llm_analyzer.SEVERITY_THRESHOLD:
                            self.stats['alerts_sent'] += 1
                    
                    # Wait before next check
                    if self.stop_event.wait(timeout=15):  # Check every 15 seconds
                        break
                        
                except Exception as e:
                    logger.error(f"Error in LLM analyzer: {e}")
                    if self.stop_event.wait(timeout=20):  # Wait before retry
                        break
                        
        except Exception as e:
            logger.error(f"Fatal error in LLM analyzer: {e}")
    
    def run_stats_reporter(self):
        """Report statistics periodically"""
        try:
            while self.running and not self.stop_event.is_set():
                # Report stats every 5 minutes
                if self.stop_event.wait(timeout=300):  # 5 minutes
                    break
                
                self.report_stats()
                
        except Exception as e:
            logger.error(f"Error in stats reporter: {e}")
    
    def report_stats(self):
        """Report current statistics"""
        try:
            uptime = time.time() - self.start_time
            uptime_hours = uptime / 3600
            
            # Get component stats
            file_stats = self.file_manager.get_processing_stats()
            audio_stats = self.audio_processor.get_processing_stats()
            llm_stats = self.llm_analyzer.get_stats()
            
            logger.info("📊 EchoWatch Status Report:")
            logger.info(f"   Uptime: {uptime_hours:.1f} hours")
            logger.info(f"   Files downloaded: {self.stats['files_downloaded']}")
            logger.info(f"   Files processed: {self.stats['files_processed']}")
            logger.info(f"   Batches analyzed: {self.stats['batches_analyzed']}")
            logger.info(f"   Alerts sent: {self.stats['alerts_sent']}")
            logger.info(f"   Inbound queue: {file_stats.get('inbound_files', 0)}")
            logger.info(f"   Processing queue: {file_stats.get('inprogress_files', 0)}")
            logger.info(f"   Transcribing queue: {file_stats.get('transcribing_files', 0)}")
            logger.info(f"   Next batch in: {llm_stats.get('next_batch_in_seconds', 0):.0f}s")
            
        except Exception as e:
            logger.error(f"Error reporting stats: {e}")
    
    def stop(self):
        """Stop all EchoWatch components"""
        if not self.running:
            return
            
        logger.info("🛑 Stopping EchoWatch...")
        self.running = False
        self.stop_event.set()
        
        # Stop Broadcastify monitor
        if self.broadcastify_monitor:
            self.broadcastify_monitor.stop()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                logger.info(f"Waiting for {thread.name} to finish...")
                thread.join(timeout=10)
                if thread.is_alive():
                    logger.warning(f"{thread.name} did not finish gracefully")
        
        # Final stats report
        logger.info("📊 Final Statistics:")
        self.report_stats()
        
        logger.info("✅ EchoWatch stopped successfully")

def main():
    """Main entry point"""
    print("🎵 EchoWatch Emergency Monitor")
    print("Real-time emergency radio monitoring and analysis")
    print("=" * 60)
    
    try:
        echowatch = EchoWatch()
        echowatch.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()