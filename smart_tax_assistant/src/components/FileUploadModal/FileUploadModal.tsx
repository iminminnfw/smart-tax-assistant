// src/components/FileUploadModal/FileUploadModal.tsx
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, FileText, X, Check, AlertCircle } from 'lucide-react';

const commonTags = ['IRS', 'Urgent', 'W-2', '1099', 'Receipts', 'Deductions', 'Investment'];

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

  // ⭐ เพิ่มฟังก์ชันสำหรับ reset state ทั้งหมด
  const resetModal = () => {
    console.log('🔄 Resetting modal state...');
    setSelectedFiles([]);
    setFileTags([]);
    setFileType('TAX_FORM');
    setDragActive(false);
    setIsUploading(false);
  };

  // ⭐ แก้ไข handleFileSelect
  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    
    console.log('Files selected:', files.length);
    
    const newItems: UploadItem[] = Array.from(files).map(file => {
      console.log('Processing file:', file.name, file.size);
      return {
        id: `${Date.now()}-${Math.random()}`,
        file: file,
        status: undefined,
        progress: 0,
      };
    });
    
    console.log('New items created:', newItems);
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

  // ⭐ แก้ไข handleUpload - ลดความซับซ้อนและปรับปรุงการปิด modal
  const handleUpload = async () => {
    const itemsToUpload = selectedFiles.filter(item => 
      item.file && (!item.status || item.status === 'error')
    );

    if (itemsToUpload.length === 0) {
      console.warn('No valid files to upload');
      return;
    }

    setIsUploading(true);
    console.log('📤 Starting upload for', itemsToUpload.length, 'files');
    
    const createdDocs: any[] = [];
    
    for (let i = 0; i < itemsToUpload.length; i++) {
      const item = itemsToUpload[i];
      
      if (!item.file) {
        console.error('Item without file in upload loop:', item);
        continue;
      }
      
      console.log(`📁 Uploading file ${i + 1}/${itemsToUpload.length}:`, item.file.name);
      
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
        console.log(`📡 Upload response for ${item.file.name}:`, response.status);

        if (response.ok) {
          const result = await response.json();
          console.log('✅ Upload successful:', result);

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
          console.error(`❌ Upload failed for ${item.file.name}:`, response.status);
          setSelectedFiles(prev => prev.map(prevItem => 
            prevItem.id === item.id ? { ...prevItem, status: 'error' as const } : prevItem
          ));
        }
      } catch (error) {
        console.error(`💥 Upload error for ${item.file.name}:`, error);
        setSelectedFiles(prev => prev.map(prevItem => 
          prevItem.id === item.id ? { ...prevItem, status: 'error' as const } : prevItem
        ));
      }
    }

    setIsUploading(false);
    console.log('🏁 Upload completed. Created docs:', createdDocs.length);

    // ⭐ ปรับปรุงการตรวจสอบความสำเร็จและปิด modal
    const successfulUploads = createdDocs.length;
    console.log('✅ Successful uploads:', successfulUploads, 'out of', itemsToUpload.length);
    
    if (successfulUploads > 0) {
      console.log('🎉 Files uploaded successfully, triggering callbacks...');
      
      // ส่ง callback กลับไปให้หน้าแม่
      if (onUploaded && createdDocs.length > 0) {
        console.log('📤 Calling onUploaded with', createdDocs.length, 'docs');
        onUploaded(createdDocs);
      } else if (onSuccess) {
        console.log('📤 Calling onSuccess');
        onSuccess();
      }
      
      // ⭐ ปิด modal ทันทีหลังจาก callback แล้ว
      console.log('🚪 Closing modal immediately...');
      
      // รอให้ UI อัพเดทแสดงสถานะ complete เล็กน้อย
      setTimeout(() => {
        resetModal(); // reset ก่อน
        onClose();    // แล้วค่อยปิด
      }, 300); // ลด delay เหลือ 300ms
    }
  };

  // ⭐ แก้ไขฟังก์ชัน onClose - เพิ่ม reset
  const handleClose = () => {
    console.log('🚪 Modal closing, resetting state...');
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
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status?: string, progress?: number) => {
    switch (status) {
      case 'uploading': return `${progress || 0}%`;
      case 'success': return 'Complete';
      case 'error': return 'Error';
      default: return '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Upload files</h2>
            <button
              onClick={handleClose} // ⭐ เปลี่ยนเป็น handleClose
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[calc(90vh-140px)] overflow-y-auto">
          {/* Drag & Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              dragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-10 h-10 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">
              <span className="font-medium">Drag and drop files here, or </span>
              <label className="text-blue-600 font-medium cursor-pointer hover:text-blue-700">
                Select files
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                  accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx,.xls,.doc,.docx"
                />
              </label>
            </p>
            <p className="text-sm text-gray-500">
              Accepted file types: PDF, JPG, PNG, CSV, XLSX, DOC (25MB each)
            </p>
          </div>

          {/* File List */}
          {selectedFiles.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">Selected Files</h3>
                <div className="flex items-center space-x-3">
                  <select
                    value={fileType}
                    onChange={(e) => setFileType(e.target.value)}
                    className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="TAX_FORM">Tax Form</option>
                    <option value="RECEIPT">Receipt</option>
                    <option value="DEDUCTION">Deduction</option>
                    <option value="INVESTMENT">Investment</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              {/* File Table Header */}
              <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-700 pb-2 border-b border-gray-200">
                <div className="col-span-5">File name</div>
                <div className="col-span-2">Size</div>
                <div className="col-span-2">Type</div>
                <div className="col-span-3">Status</div>
              </div>

              {/* File List */}
              <div className="space-y-2 mt-2 max-h-60 overflow-y-auto">
                {selectedFiles.map((item) => {
                  if (!item.file) {
                    console.warn('Item without file detected:', item);
                    return null;
                  }
                  
                  return (
                    <div key={item.id} className="grid grid-cols-12 gap-4 items-center py-3 hover:bg-gray-50 rounded-lg px-2">
                      <div className="col-span-5 flex items-center space-x-3">
                        <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="text-sm text-gray-900 truncate font-medium">
                          {item.file.name}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-sm text-gray-600">
                          {formatFileSize(item.file.size)}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-sm text-gray-600">
                          {getFileTypeFromName(item.file.name)}
                        </span>
                      </div>
                      <div className="col-span-3 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {item.status === 'uploading' && (
                            <div className="w-16 bg-gray-200 rounded-full h-1">
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
                            className="p-1 hover:bg-gray-200 rounded"
                          >
                            <X className="w-3 h-3 text-gray-400" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Tags Selection */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Tags (Optional)
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
                      className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                        fileTags.includes(tag)
                          ? 'bg-blue-100 text-blue-700 border-blue-200'
                          : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
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
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={isUploading || selectedFiles.every(item => item.status === 'success')}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Uploading...' : 'Start upload'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}