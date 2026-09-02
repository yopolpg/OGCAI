import os
import sys
import uuid
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

# Support Thai fonts on Windows
plt.rcParams["font.sans-serif"] = ["Tahoma", "Leelawadee UI", "Microsoft Sans Serif", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

from app.config import settings

logger = logging.getLogger("ogcai.sandbox_service")

# Setup cache directories
CHARTS_DIR = settings.CACHE_DIR / "charts"
SANDBOX_DIR = settings.CACHE_DIR / "sandbox"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

class SandboxService:
    def __init__(self):
        self.charts_dir = CHARTS_DIR
        self.sandbox_dir = SANDBOX_DIR

    def execute_python(self, code: str, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Execute Python code in an isolated subprocess with timeout and output capture.
        """
        temp_file = self.sandbox_dir / f"script_{uuid.uuid4().hex[:8]}.py"
        temp_file.write_text(code, encoding="utf-8")

        start_time = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(temp_file)],
                cwd=str(self.sandbox_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
                "execution_time_ms": duration_ms
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": -1,
                "execution_time_ms": timeout * 1000
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time_ms": 0
            }
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    def generate_dark_chart(
        self,
        chart_type: str,  # "line", "bar", "pie", "compound_interest"
        data: Dict[str, Any],
        title: str,
        xlabel: str = "",
        ylabel: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a modern Dark Theme chart for web display and save as PNG.
        """
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
        
        # Dark Theme Color Palette
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#111827")
        ax.grid(True, color="#1f2937", linestyle="--", linewidth=0.7, alpha=0.7)
        
        palette = ["#38bdf8", "#818cf8", "#34d399", "#f472b6", "#fbbf24", "#a78bfa"]

        try:
            if chart_type == "line":
                x = data.get("x", [])
                y = data.get("y", [])
                label = data.get("label", "Value")
                ax.plot(x, y, color=palette[0], linewidth=2.5, marker="o", markersize=4, label=label)
                if label:
                    ax.legend(facecolor="#1e293b", edgecolor="#334155")

            elif chart_type == "bar":
                labels = data.get("labels", [])
                values = data.get("values", [])
                colors = palette[:len(labels)] if len(labels) <= len(palette) else palette * (len(labels) // len(palette) + 1)
                bars = ax.bar(labels, values, color=colors[:len(labels)], width=0.55, edgecolor="#1e293b")
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f"{height:,.0f}",
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points",
                                ha="center", va="bottom", fontsize=8, color="#94a3b8")

            elif chart_type == "pie":
                labels = data.get("labels", [])
                values = data.get("values", [])
                colors = palette[:len(labels)]
                ax.pie(
                    values,
                    labels=labels,
                    autopct="%1.1f%%",
                    colors=colors,
                    startangle=140,
                    textprops={"color": "#f8fafc", "fontsize": 9},
                    wedgeprops={"edgecolor": "#0b0f19", "linewidth": 1.5}
                )

            elif chart_type == "compound_interest":
                years = data.get("years", [])
                principals = data.get("total_deposits", [])
                total_balances = data.get("total_balances", [])
                
                ax.plot(years, total_balances, color="#34d399", linewidth=2.5, label="มูลค่ารวมทั้งหมด (Total Balance)")
                ax.plot(years, principals, color="#38bdf8", linewidth=2.0, linestyle="--", label="เงินต้นสะสม (Principal)")
                ax.fill_between(years, principals, total_balances, color="#34d399", alpha=0.15, label="ดอกเบี้ยทบต้น (Interest Earned)")
                ax.legend(facecolor="#1e293b", edgecolor="#334155", loc="upper left")

            ax.set_title(title, fontsize=12, fontweight="bold", color="#f8fafc", pad=12)
            if xlabel and chart_type != "pie":
                ax.set_xlabel(xlabel, color="#94a3b8", fontsize=9)
            if ylabel and chart_type != "pie":
                ax.set_ylabel(ylabel, color="#94a3b8", fontsize=9)
            
            ax.tick_params(colors="#94a3b8", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#334155")

            filename = f"chart_{uuid.uuid4().hex[:10]}.png"
            file_path = self.charts_dir / filename
            plt.tight_layout()
            plt.savefig(file_path, facecolor=fig.get_facecolor(), edgecolor="none")
            plt.close(fig)

            return {
                "success": True,
                "filename": filename,
                "file_path": str(file_path),
                "image_url": f"/api/cache/charts/{filename}"
            }
        except Exception as e:
            plt.close(fig)
            logger.error(f"Error generating chart: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": "",
                "image_url": ""
            }

    # ---------------- Precision Mathematical Functions ----------------
    @staticmethod
    def calculate_compound_interest(
        principal: float,
        monthly_contribution: float,
        annual_rate_pct: float,
        years: int
    ) -> Dict[str, Any]:
        """
        Calculate precise compound interest month-by-month and year-by-year.
        """
        monthly_rate = (annual_rate_pct / 100) / 12
        months = years * 12
        
        yearly_years = []
        yearly_deposits = []
        yearly_balances = []
        
        current_balance = principal
        total_deposit = principal

        yearly_years.append(0)
        yearly_deposits.append(round(total_deposit, 2))
        yearly_balances.append(round(current_balance, 2))

        for m in range(1, months + 1):
            current_balance = (current_balance + monthly_contribution) * (1 + monthly_rate)
            total_deposit += monthly_contribution
            
            if m % 12 == 0:
                year_num = m // 12
                yearly_years.append(year_num)
                yearly_deposits.append(round(total_deposit, 2))
                yearly_balances.append(round(current_balance, 2))

        total_interest = current_balance - total_deposit

        return {
            "initial_principal": principal,
            "monthly_contribution": monthly_contribution,
            "annual_rate_pct": annual_rate_pct,
            "years": years,
            "final_balance": round(current_balance, 2),
            "total_deposits": round(total_deposit, 2),
            "total_interest_earned": round(total_interest, 2),
            "yearly_breakdown": {
                "years": yearly_years,
                "total_deposits": yearly_deposits,
                "total_balances": yearly_balances
            }
        }

sandbox_service = SandboxService()
