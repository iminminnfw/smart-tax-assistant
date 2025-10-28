'use client';

import { useState } from 'react';
import { X, FileText, Folder, Pencil } from 'lucide-react';

interface RenameModalProps {
  item: {
    id: string;
    name: string;
    type: 'file' | 'folder';
  };
  onClose: () => void;
  onSuccess: () => void;
}

export default function RenameModal({ item, onClose, onSuccess }: RenameModalProps) {
  const [name, setName] = useState(item.name);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Name cannot be empty');
      return;
    }

    if (trimmedName.length > 255) {
      setError('Name too long (max 255 characters)');
      return;
    }

    const invalidChars = /[\/\\:\*\?"<>\|]/;
    if (invalidChars.test(trimmedName)) {
      setError('Name contains invalid characters: / \\ : * ? " < > |');
      return;
    }

    setLoading(true);

    try {
      const endpoint = item.type === 'file'
        ? `/api/document/${item.id}/rename`
        : `/api/folder/${item.id}/rename`;

      const res = await fetch(endpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmedName }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Failed to rename');
        setLoading(false);
        return;
      }

      // Success
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Rename error:', err);
      setError('Network error. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <div className="flex items-center gap-2">
            {item.type === 'file' ? (
              <FileText className="w-5 h-5 text-blue-600" />
            ) : (
              <Folder className="w-5 h-5 text-yellow-600" />
            )}
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Rename {item.type === 'file' ? 'File' : 'Folder'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-4">
          <div className="mb-4">
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              New name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Pencil className="w-4 h-4 text-gray-400" />
              </div>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder={`Enter ${item.type} name`}
                autoFocus
                disabled={loading}
              />
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            )}
          </div>

          {/* Info */}
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-xs text-blue-800 dark:text-blue-300">
              <strong>Note:</strong> Only the display name will be changed.
              {item.type === 'file' && ' The file in storage will remain unchanged.'}
            </p>
          </div>

          {/* Footer */}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              disabled={loading || !name.trim()}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Renaming...
                </>
              ) : (
                <>
                  <Pencil className="w-4 h-4" />
                  Rename
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
