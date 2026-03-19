// src/components/FileUploadModal/FileUploadModal.tsx
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, FileText, X, Check, AlertCircle } from 'lucide-react';

const commonTags = ['แบบฟอร์มภาษี', 'ด่วน', 'ใบเสร็จ', 'ลดหย่อน', 'การลงทุน', 'ประกัน', 'กองทุน'];

interface UploadItem {
  id: string;
  file: File;
  status?: 'uploading' | 'success' | 'error';
  progress?: number;
}

export default function FileUploadModal({
  isOpen,
  onClose,
  folderId,
  onSuccess,
  onUploaded,
}: {
  isOpen: boolean;
  onClose: () => void;
  folderId?: string;
  onSuccess?: () => void;
  onUploaded?: (created: any[]) => void;
}) {
  const router = useRouter();
  const [selectedFiles, setSelectedFiles] = useState<UploadItem[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [fileType, setFileType] = useState('TAX_FORM');
  const [fileTags, setFileTags] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const resetModal = () => {
    setSelectedFiles([]);
    setFileTags([]);
    setFileType('TAX_FORM');
    setDragActive(false);
    setIsUploading(false);
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    const newItems: UploadItem[] = Array.from(files).map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file: file,
      status: undefined,
      progress: 0,
    }));

    setSelectedFiles(prev => [...prev, ...newItems]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const removeFile = (id: string) => {
    setSelectedFiles(prev => prev.filter(item => item.id !== id));
  };

  const handleUpload = async () => {
    const itemsToUpload = selectedFiles.filter(item =>
      item.file && (!item.status || item.status === 'error')
    );

    if (itemsToUpload.length === 0) return;

    setIsUploading(true);
    const createdDocs: any[] = [];

    for (let i = 0; i < itemsToUpload.length; i++) {
      const item = itemsToUpload[i];
      if (!item.file) continue;

      setSelectedFiles(prev => prev.map(prevItem =>
        prevItem.id === item.id ? { ...prevItem, status: 'uploading' as const, progress: 0 } : prevItem
      ));

      try {
        const formData = new FormData();
        formData.append('file', item.file);
        formData.append('type', fileType);
        formData.append('tags', JSON.stringify(fileTags));
        if (folderId) {
          formData.append('folderId', folderId);
        }

        const progressInterval = setInterval(() => {
          setSelectedFiles(prev => prev.map(prevItem =>
            prevItem.id === item.id && prevItem.progress !== undefined && prevItem.progress < 90
              ? { ...prevItem, progress: prevItem.progress + 10 }
              : prevItem
          ));
        }, 200);

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
          credentials: 'include',
        });

        clearInterval(progressInterval);

        if (response.ok) {
          const result = await response.json();
          createdDocs.push(result.document ?? {
            id: result.id,
            url: result.url,
            name: item.file.name,
            ...result
          });

          setSelectedFiles(prev => prev.map(prevItem =>
            prevItem.id === item.id ? { ...prevItem, status: 'success' as const, progress: 100 } : prevItem
          ));
        } else {
          setSelectedFiles(prev => prev.map(prevItem =>
            prevItem.id === item.id ? { ...prevItem, status: 'error' as const } : prevItem
          ));
        }
      } catch (error) {
        setSelectedFiles(prev => prev.map(prevItem =>
          prevItem.id === item.id ? { ...prevItem, status: 'error' as const } : prevItem
        ));
      }
    }

    setIsUploading(false);

    const successfulUploads = createdDocs.length;

    if (successfulUploads > 0) {
      if (onUploaded && createdDocs.length > 0) {
        onUploaded(createdDocs);
      } else if (onSuccess) {
        onSuccess();
      }

      setTimeout(() => {
        resetModal();
        onClose();
      }, 300);
    }
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileTypeFromName = (fileName?: string) => {
    if (!fileName) return 'FILE';
    const ext = fileName.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return 'PDF';
      case 'jpg':
      case 'jpeg': return 'JPG';
      case 'png': return 'PNG';
      case 'csv': return 'CSV';
      case 'xlsx':
      case 'xls': return 'XLSX';
      case 'doc':
      case 'docx': return 'DOC';
      default: return ext?.toUpperCase() || 'FILE';
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'uploading': return 'text-blue-600';
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-slate-600';
    }
  };

  const getStatusText = (status?: string, progress?: number) => {
    switch (status) {
      case 'uploading': return `${progress || 0}%`;
      case 'success': return 'สำเร็จ';
      case 'error': return 'ผิดพลาด';
      default: return '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">อัปโหลดไฟล์</h2>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[calc(90vh-140px)] overflow-y-auto">
          {/* Drag & Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-slate-300 hover:border-slate-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-10 h-10 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-600 mb-2">
              <span className="font-medium">ลากและวางไฟล์ที่นี่ หรือ </span>
              <label className="text-blue-600 font-medium cursor-pointer hover:text-blue-700">
                เลือกไฟล์
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                  accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx,.xls,.doc,.docx"
                />
              </label>
            </p>
            <p className="text-sm text-slate-500">
              รองรับไฟล์: PDF, JPG, PNG, CSV, XLSX, DOC (สูงสุด 25MB ต่อไฟล์)
            </p>
          </div>

          {/* File List */}
          {selectedFiles.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-slate-800">ไฟล์ที่เลือก</h3>
                <div className="flex items-center space-x-3">
                  <select
                    value={fileType}
                    onChange={(e) => setFileType(e.target.value)}
                    className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="TAX_FORM">แบบฟอร์มภาษี</option>
                    <option value="RECEIPT">ใบเสร็จ</option>
                    <option value="DEDUCTION">ลดหย่อนภาษี</option>
                    <option value="INVESTMENT">การลงทุน</option>
                    <option value="OTHER">อื่นๆ</option>
                  </select>
                </div>
              </div>

              {/* File Table Header */}
              <div className="grid grid-cols-12 gap-4 text-sm font-medium text-slate-600 pb-2 border-b border-slate-200">
                <div className="col-span-5">ชื่อไฟล์</div>
                <div className="col-span-2">ขนาด</div>
                <div className="col-span-2">ประเภท</div>
                <div className="col-span-3">สถานะ</div>
              </div>

              {/* File List */}
              <div className="space-y-2 mt-2 max-h-60 overflow-y-auto">
                {selectedFiles.map((item) => {
                  if (!item.file) return null;

                  return (
                    <div key={item.id} className="grid grid-cols-12 gap-4 items-center py-3 hover:bg-slate-50 rounded-lg px-2">
                      <div className="col-span-5 flex items-center space-x-3">
                        <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <span className="text-sm text-slate-800 truncate font-medium">
                          {item.file.name}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-sm text-slate-600">
                          {formatFileSize(item.file.size)}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-sm text-slate-600">
                          {getFileTypeFromName(item.file.name)}
                        </span>
                      </div>
                      <div className="col-span-3 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {item.status === 'uploading' && (
                            <div className="w-16 bg-slate-200 rounded-full h-1">
                              <div
                                className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                                style={{ width: `${item.progress || 0}%` }}
                              ></div>
                            </div>
                          )}
                          {item.status === 'success' && (
                            <Check className="w-4 h-4 text-green-600" />
                          )}
                          {item.status === 'error' && (
                            <AlertCircle className="w-4 h-4 text-red-600" />
                          )}
                          <span className={`text-sm font-medium ${getStatusColor(item.status)}`}>
                            {getStatusText(item.status, item.progress)}
                          </span>
                        </div>
                        {!item.status && (
                          <button
                            onClick={() => removeFile(item.id)}
                            className="p-1 hover:bg-slate-200 rounded"
                          >
                            <X className="w-3 h-3 text-slate-400" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Tags Selection */}
              <div className="mt-4 pt-4 border-t border-slate-200">
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  แท็ก (ไม่บังคับ)
                </label>
                <div className="flex flex-wrap gap-2">
                  {commonTags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => {
                        if (fileTags.includes(tag)) {
                          setFileTags(fileTags.filter(t => t !== tag));
                        } else {
                          setFileTags([...fileTags, tag]);
                        }
                      }}
                      className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                        fileTags.includes(tag)
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {selectedFiles.length > 0 && (
          <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">
            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={isUploading || selectedFiles.every(item => item.status === 'success')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'กำลังอัปโหลด...' : 'เริ่มอัปโหลด'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
