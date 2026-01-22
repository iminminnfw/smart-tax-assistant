'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppNavigation } from '@/components/AppNavigation';
import {
  Trash2,
  RotateCcw,
  XCircle,
  Folder,
  File,
  Clock,
  AlertTriangle,
  Home
} from 'lucide-react';

interface TrashItem {
  id: string;
  name: string;
  deletedAt: string;
  type: 'file' | 'folder';
  folderId?: string;
}

interface TrashData {
  folders: Array<{
    id: string;
    name: string;
    deletedAt: string;
    color: string;
  }>;
  files: Array<{
    id: string;
    name: string;
    deletedAt: string;
    folderId: string | null;
  }>;
}

export default function TrashPage() {
  const router = useRouter();
  const [trashItems, setTrashItems] = useState<TrashItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEmptyConfirm, setShowEmptyConfirm] = useState(false);

  useEffect(() => {
    fetchTrashItems();
  }, []);

  const fetchTrashItems = async () => {
    try {
      const res = await fetch('/api/trash');
      if (res.ok) {
        const data: TrashData = await res.json();

        const items: TrashItem[] = [
          ...data.folders.map(f => ({
            id: f.id,
            name: f.name,
            deletedAt: f.deletedAt,
            type: 'folder' as const
          })),
          ...data.files.map(f => ({
            id: f.id,
            name: f.name,
            deletedAt: f.deletedAt,
            type: 'file' as const,
            folderId: f.folderId || undefined
          }))
        ];

        setTrashItems(items);
      }
    } catch (error) {
      console.error('Failed to fetch trash items:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (id: string, type: 'file' | 'folder') => {
    try {
      const res = await fetch('/api/trash/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, type })
      });

      if (res.ok) {
        setTrashItems(items => items.filter(item => item.id !== id));
        alert(`${type === 'folder' ? 'Folder' : 'File'} restored successfully!`);
      } else {
        alert('Failed to restore item');
      }
    } catch (error) {
      console.error('Error restoring item:', error);
      alert('Error restoring item');
    }
  };

  const handleDeletePermanently = async (id: string, type: 'file' | 'folder') => {
    if (!confirm(`Are you sure you want to permanently delete this ${type}? This action cannot be undone.`)) {
      return;
    }

    try {
      const res = await fetch('/api/trash/permanent', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, type })
      });

      if (res.ok) {
        setTrashItems(items => items.filter(item => item.id !== id));
        alert('Item permanently deleted');
      } else {
        alert('Failed to delete item');
      }
    } catch (error) {
      console.error('Error deleting item:', error);
      alert('Error deleting item');
    }
  };

  const handleEmptyTrash = async () => {
    if (!showEmptyConfirm) {
      setShowEmptyConfirm(true);
      return;
    }

    try {
      const res = await fetch('/api/trash', {
        method: 'DELETE'
      });

      if (res.ok) {
        const data = await res.json();
        setTrashItems([]);
        setShowEmptyConfirm(false);
        alert(`Deleted ${data.deletedFiles} files and ${data.deletedFolders} folders`);
      } else {
        alert('Failed to empty trash');
      }
    } catch (error) {
      console.error('Error emptying trash:', error);
      alert('Error emptying trash');
    }
  };

  const getDaysRemaining = (deletedAt: string) => {
    const deleted = new Date(deletedAt);
    const now = new Date();
    const daysPassed = Math.floor((now.getTime() - deleted.getTime()) / (1000 * 60 * 60 * 24));
    const daysRemaining = 7 - daysPassed;
    return Math.max(0, daysRemaining);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-slate-600">Loading trash...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AppNavigation />

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Trash2 className="w-8 h-8 text-slate-700" />
              <div>
                <h1 className="text-2xl font-semibold text-slate-800">ถังขยะ</h1>
                <p className="text-sm text-slate-500">จัดการไฟล์ที่ถูกลบ</p>
              </div>
            </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/document')}
              className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
              title="กลับหน้าหลัก"
            >
              <Home className="w-4 h-4" />
              <span>หน้าหลัก</span>
            </button>

            {trashItems.length > 0 && (
              <button
                onClick={handleEmptyTrash}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 text-sm font-medium"
              >
                <Trash2 className="w-4 h-4" />
                <span>ล้างถังขยะ</span>
              </button>
            )}
          </div>
        </div>

        {/* Warning Banner */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-amber-800">
            <strong>Items in trash will be permanently deleted after 7 days.</strong>
            <br />
            You can restore items at any time before they are automatically deleted.
          </div>
        </div>
      </div>

      {/* Empty Trash Confirmation */}
      {showEmptyConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Empty Trash?</h3>
            <p className="text-slate-600 text-sm mb-6">
              This will permanently delete all items in trash (older than 7 days). This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowEmptyConfirm(false)}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleEmptyTrash}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              >
                Empty Trash
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Trash Items List */}
      {trashItems.length === 0 ? (
        <div className="text-center py-16">
          <Trash2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-600 mb-2">Trash is empty</h3>
          <p className="text-slate-500 text-sm">Deleted items will appear here</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Deleted
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Days Remaining
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {trashItems.map((item) => {
                const daysRemaining = getDaysRemaining(item.deletedAt);

                return (
                  <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {item.type === 'folder' ? (
                          <Folder className="w-5 h-5 text-blue-500" />
                        ) : (
                          <File className="w-5 h-5 text-slate-400" />
                        )}
                        <span className="font-medium text-slate-800">{item.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 capitalize">
                      {item.type}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {new Date(item.deletedAt).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`font-medium ${
                        daysRemaining <= 2 ? 'text-red-600' :
                        daysRemaining <= 4 ? 'text-amber-600' :
                        'text-green-600'
                      }`}>
                        {daysRemaining} {daysRemaining === 1 ? 'day' : 'days'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleRestore(item.id, item.type)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Restore"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeletePermanently(item.id, item.type)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete Permanently"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      </div>
    </div>
  );
}
