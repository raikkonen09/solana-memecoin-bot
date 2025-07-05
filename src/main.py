
import time
import random
import os
from src.monitoring import DexMonitor
from src.analyzer import OnChainAnalyzer
from src.notifier import TelegramNotifier

class MemecoinBot:
    def __init__(self, telegram_bot_token=None, telegram_chat_id=None):
        self.monitor = DexMonitor()
        self.analyzer = OnChainAnalyzer()
        self.notifier = None
        if telegram_bot_token and telegram_chat_id:
            self.notifier = TelegramNotifier(telegram_bot_token, telegram_chat_id)

        self.wallet_balance_sol = 10.0 # Starting balance
        self.investment_per_trade_sol = 0.1 # Small investment for demo
        self.target_profit_multiplier = 2.0
        self.stop_loss_percentage = 0.30 # 30% loss
        self.active_positions = {}

    def send_notification(self, message):
        if self.notifier:
            self.notifier.send_message(message)
        else:
            print(f"[NOTIFICATION] {message}") # Fallback to print if notifier not configured

    def run(self):
        self.send_notification("--- Starting Solana Memecoin Trading Bot ---")
        self.send_notification(f"Initial SOL Balance: {self.wallet_balance_sol}")

        while True:
            self.send_notification("\n--- Monitoring for new tokens ---")
            # Simulate getting new listings from Dexscreener
            dexscreener_pairs = self.monitor.get_new_dexscreener_pairs()
            for pair in dexscreener_pairs:
                token_info = {
                    "name": pair["baseToken"]["symbol"],
                    "address": pair["pairAddress"], # Using pair address as token address for simplicity in mock
                    "initial_price": pair["fdv"] / pair["liquidity"]["usd"] if pair["liquidity"]["usd"] > 0 else 0.000001, # Mock price
                    "current_price": None
                }
                self.send_notification(f"[BOT] Detected potential new token from Dexscreener: {token_info['name']}")
                self.process_new_token(token_info)

            # Simulate getting new listings from Birdeye
            birdeye_listing = self.monitor.get_new_birdeye_listings()
            if birdeye_listing:
                token_info = {
                    "name": birdeye_listing["symbol"],
                    "address": birdeye_listing["address"],
                    "initial_price": birdeye_listing["liquidity"] / birdeye_listing["market_cap"] if birdeye_listing["market_cap"] > 0 else 0.000001, # Mock price
                    "current_price": None
                }
                self.send_notification(f"[BOT] Detected potential new token from Birdeye: {token_info['name']}")
                self.process_new_token(token_info)

            # Simulate getting new listings from GeckoTerminal
            geckoterminal_pools = self.monitor.get_new_geckoterminal_pools()
            for pool in geckoterminal_pools:
                token_info = {
                    "name": pool["attributes"]["base_token_symbol"],
                    "address": pool["id"], # Using pool ID as token address for simplicity in mock
                    "initial_price": pool["attributes"]["reserve_in_usd"] / pool["attributes"]["volume_usd"]["h24"] if pool["attributes"]["volume_usd"]["h24"] > 0 else 0.000001, # Mock price
                    "current_price": None
                }
                self.send_notification(f"[BOT] Detected potential new token from GeckoTerminal: {token_info['name']}")
                self.process_new_token(token_info)

            # Monitor active positions and attempt to sell
            self.monitor_and_sell_positions()

            time.sleep(5) # Wait before next monitoring cycle

    def process_new_token(self, token_info):
        self.send_notification(f"Processing new token: {token_info['name']}")
        if self.filter_token(token_info):
            self.send_notification(f"[BOT] Token {token_info['name']} passed filters. Attempting to buy...")
            if self.wallet_balance_sol >= self.investment_per_trade_sol:
                # Simulate buy transaction
                token_info["current_price"] = token_info["initial_price"]
                self.active_positions[token_info["address"]] = token_info
                self.wallet_balance_sol -= self.investment_per_trade_sol
                self.send_notification(f"[BOT] Successfully bought {self.investment_per_trade_sol / token_info['initial_price']:.2f} {token_info['name']}. Remaining SOL: {self.wallet_balance_sol:.4f}")
            else:
                self.send_notification("[BOT] Insufficient SOL balance to make a trade.")
        else:
            self.send_notification(f"[BOT] Token {token_info['name']} failed filters. Skipping.")

    def filter_token(self, token_info):
        self.send_notification(f"  - Checking LP Locked...")
        lp_locked = self.analyzer.check_lp_locked(token_info["address"])
        if not lp_locked:
            self.send_notification("    -> Failed: LP not locked.")
            return False

        self.send_notification(f"  - Simulating Buy Transaction for Tax Check...")
        buy_sim_result = self.analyzer.simulate_transaction(token_info["address"], "buy")
        if not buy_sim_result["success"] or buy_sim_result["blacklist"] or buy_sim_result["tax"] > 0.10:
            self.send_notification(f"    -> Failed: Buy simulation failed (success: {buy_sim_result['success']}, blacklist: {buy_sim_result['blacklist']}, tax: {buy_sim_result['tax']:.2f}).")
            return False
        token_info["buy_tax"] = buy_sim_result["tax"]
        self.send_notification(f"    -> Buy Tax: {token_info['buy_tax']:.2f}")

        self.send_notification(f"  - Simulating Sell Transaction for Tax Check...")
        sell_sim_result = self.analyzer.simulate_transaction(token_info["address"], "sell")
        if not sell_sim_result["success"] or sell_sim_result["blacklist"] or sell_sim_result["tax"] > 0.10:
            self.send_notification(f"    -> Failed: Sell simulation failed (success: {sell_sim_result['success']}, blacklist: {sell_sim_result['blacklist']}, tax: {sell_sim_result['tax']:.2f}).")
            return False
        token_info["sell_tax"] = sell_sim_result["tax"]
        self.send_notification(f"    -> Sell Tax: {token_info['sell_tax']:.2f}")

        self.send_notification(f"  - Analyzing Holder Distribution...")
        holder_analysis = self.analyzer.analyze_holder_distribution(token_info["address"])
        if holder_analysis["has_large_holder"]:
            self.send_notification("    -> Warning: Large holder detected. Proceed with caution or skip.")
            # For this demo, we will still proceed, but in a real bot, this might be a reason to skip.

        self.send_notification("  -> All filters passed.")
        return True

    def monitor_and_sell_positions(self):
        self.send_notification("\n--- Monitoring active positions ---")
        positions_to_remove = []
        for address, position in list(self.active_positions.items()):
            # Simulate price fluctuation for active positions
            current_price = position["current_price"] * random.uniform(0.8, 2.5) 
            position["current_price"] = current_price

            target_price = position["initial_price"] * self.target_profit_multiplier
            stop_loss_price = position["initial_price"] * (1 - self.stop_loss_percentage)

            self.send_notification(f"Monitoring {position['name']}. Current: {current_price:.6f}, Initial: {position['initial_price']:.6f}, Target: {target_price:.6f}, Stop-Loss: {stop_loss_price:.6f}")

            if current_price >= target_price:
                profit = (current_price - position["initial_price"]) / position["initial_price"]
                self.send_notification(f"[BOT] Selling {position['name']} at {current_price:.6f} SOL/token. Profit: {profit:.2f}x (Target Reached)")
                self.wallet_balance_sol += (self.investment_per_trade_sol / position["initial_price"]) * current_price * (1 - position.get("sell_tax", 0))
                positions_to_remove.append(address)
            elif current_price <= stop_loss_price:
                loss = (position["initial_price"] - current_price) / position["initial_price"]
                self.send_notification(f"[BOT] Selling {position['name']} at {current_price:.6f} SOL/token. Loss: {loss:.2f}x (Stop-Loss Triggered)")
                self.wallet_balance_sol += (self.investment_per_trade_sol / position["initial_price"]) * current_price * (1 - position.get("sell_tax", 0))
                positions_to_remove.append(address)
            else:
                self.send_notification(f"[BOT] {position['name']} still active.")
        
        for address in positions_to_remove:
            del self.active_positions[address]

        self.send_notification(f"Current SOL Balance: {self.wallet_balance_sol:.4f}")
        self.send_notification(f"Active Positions: {len(self.active_positions)}")


if __name__ == "__main__":
    # In a real scenario, these would be loaded from environment variables or a config file
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    bot = MemecoinBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    bot.run()


