import React, { useState, useEffect } from 'react';
import { DollarSign, PieChart, TrendingUp, Plus, ArrowUpRight, ArrowDownRight, Wallet, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { FinanceSummaryData } from '../../types';

export const FinanceTab: React.FC = () => {
  const [summary, setSummary] = useState<FinanceSummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [quickInput, setQuickInput] = useState('');
  const [parsedPreview, setParsedPreview] = useState<any>(null);

  // Compound Interest Inputs
  const [principal, setPrincipal] = useState(50000);
  const [monthlyContribution, setMonthlyContribution] = useState(3000);
  const [rate, setRate] = useState(7);
  const [years, setYears] = useState(5);
  const [compoundResult, setCompoundResult] = useState<any>(null);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await api.getFinanceSummary();
      setSummary(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const handleParseInput = async (val: string) => {
    setQuickInput(val);
    if (val.trim().length > 3) {
      try {
        const parsed = await api.parseFinanceText(val);
        setParsedPreview(parsed);
      } catch (e) {
        setParsedPreview(null);
      }
    } else {
      setParsedPreview(null);
    }
  };

  const handleSaveTransaction = async (previewData = parsedPreview) => {
    if (!previewData || previewData.amount <= 0) return;
    try {
      await api.addFinanceTransaction(previewData);
      setQuickInput('');
      setParsedPreview(null);
      await loadSummary();
    } catch (e) {
      console.error(e);
    }
  };

  const handleQuickSubmit = async () => {
    if (parsedPreview && parsedPreview.amount > 0) {
      await handleSaveTransaction(parsedPreview);
    } else if (quickInput.trim().length > 2) {
      try {
        const parsed = await api.parseFinanceText(quickInput.trim());
        if (parsed && parsed.amount > 0) {
          await handleSaveTransaction(parsed);
        }
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleCalculateCompound = async () => {
    try {
      const res = await api.calculateCompoundGrowth({
        principal: Number(principal),
        monthly_contribution: Number(monthlyContribution),
        annual_rate_pct: Number(rate),
        years: Number(years)
      });
      setCompoundResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-4 text-xs overflow-y-auto pr-1 h-full">
      {/* 1. Quick NLP Transaction Entry */}
      <div className="glass-card p-3 rounded-xl border border-slate-800">
        <p className="font-semibold text-slate-200 mb-1.5 flex items-center gap-1.5">
          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          บันทึกรายรับ-จ่ายด่วน (NLP)
        </p>
        <div className="flex gap-1.5">
          <input
            type="text"
            placeholder="เช่น 'จ่ายค่ากาแฟ 65 บาท', 'เงินเดือนเข้า 45000'"
            value={quickInput}
            onChange={(e) => handleParseInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleQuickSubmit();
              }
            }}
            className="flex-1 glass-input px-2.5 py-1.5 rounded-lg text-xs"
          />
          <button
            onClick={() => handleSaveTransaction()}
            disabled={!parsedPreview || parsedPreview.amount <= 0}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-medium transition-all"
            title="บันทึกรายการ (กด Enter)"
          >
            บันทึก
          </button>
        </div>

        {/* NLP Live Preview Tag */}
        {parsedPreview && (
          <div className="mt-2 p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] flex items-center justify-between">
            <span className="text-slate-300">
              หมวด: <span className="text-cyan-300 font-semibold">{parsedPreview.category}</span> ({parsedPreview.type})
            </span>
            <span className={`font-bold ${parsedPreview.type === 'income' ? 'text-emerald-400' : 'text-rose-400'}`}>
              {parsedPreview.type === 'income' ? '+' : '-'}{parsedPreview.amount.toLocaleString()} ฿
            </span>
          </div>
        )}
      </div>

      {/* 2. Monthly Summary Cards */}
      <div className="glass-card p-3 rounded-xl border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <p className="font-semibold text-slate-200 flex items-center gap-1.5">
            <Wallet className="w-3.5 h-3.5 text-cyan-400" />
            ภาพรวมการเงินประจำเดือน
          </p>
          <button onClick={loadSummary} className="text-slate-400 hover:text-cyan-300">
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {summary ? (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <ArrowUpRight className="w-2.5 h-2.5 text-emerald-400" /> รายรับรวม
                </span>
                <p className="text-sm font-bold text-emerald-400">+{summary.total_income.toLocaleString()} ฿</p>
              </div>
              <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <ArrowDownRight className="w-2.5 h-2.5 text-rose-400" /> รายจ่ายรวม
                </span>
                <p className="text-sm font-bold text-rose-400">-{summary.total_expense.toLocaleString()} ฿</p>
              </div>
            </div>

            <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400">เงินออมสุทธิ</span>
                <p className="text-xs font-bold text-cyan-300">+{summary.net_balance.toLocaleString()} ฿</p>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-slate-400">อัตราการออม</span>
                <p className="text-xs font-bold text-emerald-400">{summary.savings_rate_pct}%</p>
              </div>
            </div>

            {/* Render Category Breakdown Chart if available */}
            {summary.chart?.success && summary.chart.image_url && (
              <div className="mt-2 rounded-xl overflow-hidden border border-slate-800">
                <img src={summary.chart.image_url} alt="สัดส่วนค่าใช้จ่าย" className="w-full h-auto" />
              </div>
            )}
          </div>
        ) : (
          <p className="text-center py-4 text-slate-500">กำลังโหลดข้อมูลสรุป...</p>
        )}
      </div>

      {/* 3. Compound Interest Simulation Calculator */}
      <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
        <p className="font-semibold text-slate-200 flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
          จำลองดอกเบี้ยทบต้น (Compound Interest)
        </p>

        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <label className="text-slate-400">เงินต้นเริ่มต้น (฿)</label>
            <input
              type="number"
              value={principal}
              onChange={(e) => setPrincipal(Number(e.target.value))}
              onKeyDown={(e) => e.key === 'Enter' && handleCalculateCompound()}
              className="w-full glass-input px-2 py-1 rounded text-xs mt-0.5"
            />
          </div>
          <div>
            <label className="text-slate-400">ออมเพิ่มต่อเดือน (฿)</label>
            <input
              type="number"
              value={monthlyContribution}
              onChange={(e) => setMonthlyContribution(Number(e.target.value))}
              onKeyDown={(e) => e.key === 'Enter' && handleCalculateCompound()}
              className="w-full glass-input px-2 py-1 rounded text-xs mt-0.5"
            />
          </div>
          <div>
            <label className="text-slate-400">ผลตอบแทน (%/ปี)</label>
            <input
              type="number"
              value={rate}
              onChange={(e) => setRate(Number(e.target.value))}
              onKeyDown={(e) => e.key === 'Enter' && handleCalculateCompound()}
              className="w-full glass-input px-2 py-1 rounded text-xs mt-0.5"
            />
          </div>
          <div>
            <label className="text-slate-400">ระยะเวลา (ปี)</label>
            <input
              type="number"
              value={years}
              onChange={(e) => setYears(Number(e.target.value))}
              onKeyDown={(e) => e.key === 'Enter' && handleCalculateCompound()}
              className="w-full glass-input px-2 py-1 rounded text-xs mt-0.5"
            />
          </div>
        </div>

        <button
          onClick={handleCalculateCompound}
          className="w-full py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-purple-600/20 transition-all mt-1"
        >
          📈 คำนวณและสร้างกราฟพอร์ต
        </button>

        {compoundResult && (
          <div className="mt-2 space-y-2">
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
              <div className="flex justify-between">
                <span className="text-slate-400">มูลค่าพอร์ตสะสม:</span>
                <span className="text-emerald-400 font-bold">{compoundResult.final_balance?.toLocaleString()} ฿</span>
              </div>
              <div className="flex justify-between text-[10px] mt-0.5">
                <span className="text-slate-400">ดอกเบี้ยทบต้นที่ได้รับ:</span>
                <span className="text-cyan-300">+{compoundResult.total_interest_earned?.toLocaleString()} ฿</span>
              </div>
            </div>

            {compoundResult.chart?.image_url && (
              <div className="rounded-xl overflow-hidden border border-slate-800">
                <img src={compoundResult.chart.image_url} alt="กราฟดอกเบี้ยทบต้น" className="w-full h-auto" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
