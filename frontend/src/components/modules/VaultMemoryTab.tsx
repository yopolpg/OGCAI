import React, { useState, useEffect } from 'react';
import { Database, Star, FolderOpen, Upload, Search, RefreshCw, Trash2, Plus, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { UserProfileItem, StarredKnowledgeItem, VaultFileItem } from '../../types';

export const VaultMemoryTab: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'profile' | 'starred' | 'vault'>('vault');

  // User Profile State
  const [profileFacts, setProfileFacts] = useState<UserProfileItem[]>([]);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');

  // Starred State
  const [starredItems, setStarredItems] = useState<StarredKnowledgeItem[]>([]);

  // Vault Files State
  const [vaultFiles, setVaultFiles] = useState<VaultFileItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [indexing, setIndexing] = useState(false);
  const [uploading, setUploading] = useState(false);

  const loadData = async () => {
    try {
      const [facts, starred, filesData] = await Promise.all([
        api.getUserProfile(),
        api.getStarredKnowledge(),
        api.getVaultFiles()
      ]);
      setProfileFacts(facts || []);
      setStarredItems(starred || []);
      setVaultFiles(filesData?.files || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddProfileFact = async () => {
    if (!newKey.trim() || !newValue.trim()) return;
    try {
      await api.setUserProfileFact(newKey.trim(), newValue.trim());
      setNewKey('');
      setNewValue('');
      const facts = await api.getUserProfile();
      setProfileFacts(facts);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteProfileFact = async (id: number) => {
    try {
      await api.deleteUserProfileFact(id);
      setProfileFacts(profileFacts.filter((f) => f.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteStarred = async (id: string) => {
    try {
      await api.deleteStarredKnowledge(id);
      setStarredItems(starredItems.filter((s) => s.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleIndexVault = async () => {
    setIndexing(true);
    try {
      await api.indexVault();
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setIndexing(false);
    }
  };

  const handleSearchVault = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await api.searchVault(searchQuery, 3);
      setSearchResults(res.results || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.uploadVaultFile(file);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-full space-y-3 text-xs">
      {/* Sub-tab Navigation */}
      <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => setActiveSubTab('vault')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-all ${
            activeSubTab === 'vault' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          📂 Vault (150GB+)
        </button>
        <button
          onClick={() => setActiveSubTab('profile')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-all ${
            activeSubTab === 'profile' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          🧠 Profile Facts
        </button>
        <button
          onClick={() => setActiveSubTab('starred')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-all ${
            activeSubTab === 'starred' ? 'bg-amber-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          ⭐ Starred ({starredItems.length})
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        {/* SUBTAB 1: Document Vault */}
        {activeSubTab === 'vault' && (
          <div className="space-y-3">
            {/* Upload Zone & Index Button */}
            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-slate-200">คลังเอกสารส่วนตัว (150GB+)</p>
                <button
                  onClick={handleIndexVault}
                  disabled={indexing}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[10px]"
                  title="ทำ Index เวกเตอร์ใหม่"
                >
                  <RefreshCw className={`w-3 h-3 ${indexing ? 'animate-spin' : ''}`} />
                  <span>Re-index</span>
                </button>
              </div>

              {/* Upload Input */}
              <label className="border border-dashed border-slate-700 hover:border-cyan-500 rounded-xl p-3 flex flex-col items-center justify-center gap-1 cursor-pointer transition-colors bg-slate-900/40">
                <Upload className="w-5 h-5 text-cyan-400" />
                <span className="text-[11px] text-slate-300">
                  {uploading ? 'กำลังอัปโหลดและทำ Index...' : 'คลิกเพื่อเลือกไฟล์เอกสาร (PDF, MD, CSV, TXT)'}
                </span>
                <input type="file" onChange={handleFileUpload} className="hidden" accept=".pdf,.md,.txt,.csv,.json,.py" />
              </label>
            </div>

            {/* Semantic Search */}
            <div className="glass-card p-2.5 rounded-xl border border-slate-800 flex gap-1.5">
              <input
                type="text"
                placeholder="ค้นหาเอกสารแบบ Semantic Vector Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchVault()}
                className="flex-1 glass-input px-2.5 py-1.5 rounded-lg text-xs"
              />
              <button
                onClick={handleSearchVault}
                className="p-1.5 px-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white"
              >
                <Search className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-[10px] font-semibold text-cyan-400 px-1">ผลลัพธ์การค้นหาความหมาย:</p>
                {searchResults.map((r, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-1">
                    <p className="font-semibold text-cyan-300 text-[11px]">{r.filename}</p>
                    <p className="text-[10px] text-slate-300 line-clamp-3">{r.content}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Files List */}
            <div className="space-y-1">
              <p className="text-[10px] font-semibold text-slate-400 px-1">ไฟล์ในคลัง ({vaultFiles.length} ไฟล์):</p>
              {vaultFiles.map((f) => (
                <div key={f.name} className="p-2 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span className="truncate text-slate-200 text-[11px]">{f.name}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 whitespace-nowrap">{f.size_kb} KB</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SUBTAB 2: User Profile */}
        {activeSubTab === 'profile' && (
          <div className="space-y-3">
            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
              <p className="font-semibold text-slate-200">เพิ่มข้อมูลส่วนตัวที่ต้องการให้ AI จำ</p>
              <div className="flex gap-1.5">
                <input
                  type="text"
                  placeholder="หัวข้อ (เช่น user_name, career)"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddProfileFact()}
                  className="w-1/3 glass-input px-2 py-1 rounded text-xs"
                />
                <input
                  type="text"
                  placeholder="รายละเอียด..."
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddProfileFact()}
                  className="flex-1 glass-input px-2 py-1 rounded text-xs"
                />
                <button
                  onClick={handleAddProfileFact}
                  className="p-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
                  title="บันทึกข้อมูล (กด Enter)"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold text-slate-400 px-1">สิ่งที่ AI จำเกี่ยวกับคุณ:</p>
              {profileFacts.map((fact) => (
                <div key={fact.id} className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-cyan-400 font-semibold">{fact.key}</span>: <span className="text-slate-200">{fact.value}</span>
                  </div>
                  <button
                    onClick={() => handleDeleteProfileFact(fact.id)}
                    className="p-1 rounded text-slate-500 hover:text-rose-400"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SUBTAB 3: Starred Knowledge */}
        {activeSubTab === 'starred' && (
          <div className="space-y-2">
            {starredItems.length === 0 ? (
              <p className="text-center py-8 text-slate-500">ยังไม่มีคำตอบที่บันทึกไว้ (คลิกปุ่ม ⭐ ในแชทเพื่อบันทึก)</p>
            ) : (
              starredItems.map((item) => (
                <div key={item.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-amber-300 flex items-center gap-1.5">
                      <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                      {item.title}
                    </p>
                    <button
                      onClick={() => handleDeleteStarred(item.id)}
                      className="p-1 text-slate-500 hover:text-rose-400"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-300 whitespace-pre-wrap">{item.content}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
