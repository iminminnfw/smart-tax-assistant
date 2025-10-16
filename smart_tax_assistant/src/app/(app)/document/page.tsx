'use client';

import React, { useState, useEffect } from 'react';
import { useRouter , useSearchParams} from 'next/navigation';
import { useSession } from 'next-auth/react';
import FileUploadModal from '@/components/FileUploadModal/FileUploadModal';
import {
  FolderPlus,
  Search,
  Grid3X3,
  List,
  MoreHorizontal,
  Folder,
  FileText,
  Palette,
  Tag,
  Upload,
  Clock,
  Filter,
  SortAsc,
  Home,
  Sparkles,
  Trash2,
  AlertTriangle, // เพิ่ม icon ใหม่
} from 'lucide-react';

interface DocumentFolder {
  id: string;
  name: string;
  color: string;
  files: DocumentFile[];
  children: DocumentFolder[];
  createdAt: string;
  updatedAt: string;
}

interface DocumentFile {
  id: string;
  name: string;
  type: string;
  tags: string[];
  folderId?: string;
  createdAt: string;
  updatedAt: string;
  isUploaded?: boolean;
  fileUrl?: string;
  fileName?: string;
  fileSize?: number;
  mimeType?: string;
}

const predefinedColors = [
  '#EF4444', '#F97316', '#EAB308', '#22C55E', 
  '#06B6D4', '#3B82F6', '#8B5CF6', '#EC4899', '#6B7280'
];

const commonTags = ['IRS', 'Urgent', 'W-2', '1099', 'Receipts', 'Deductions', 'Investment'];

export default function DocumentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session } = useSession();
  const [folders, setFolders] = useState<DocumentFolder[]>([]);
  const [files, setFiles] = useState<DocumentFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<DocumentFolder | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  
  // Modal states
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState<string | null>(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showDeleteFolderConfirm, setShowDeleteFolderConfirm] = useState<string | null>(null); // ⭐ เพิ่ม state สำหรับลบโฟลเดอร์
  
  // Form states
  const [folderName, setFolderName] = useState('');
  const [folderColor, setFolderColor] = useState('#3B82F6');

  const handleGoHome = () => {
    router.push('/WelcomeHome');
  };

  // Fetch data
  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const folderId = searchParams.get('folder');
    if (folderId && folders.length > 0) {
      const folder = folders.find(f => f.id === folderId);
      if (folder) {
        setSelectedFolder(folder);
      }
    }
  }, [searchParams, folders]);

  const fetchData = async () => {
    try {
      const [foldersRes, filesRes] = await Promise.all([
        fetch('/api/folder', { cache: 'no-store' }),
        fetch('/api/document', { cache: 'no-store' }),
      ]);

      if (foldersRes.ok) {
        const foldersData = await foldersRes.json();
        setFolders(foldersData);
      }

      if (filesRes.ok) {
        const raw = await filesRes.json();
        const list = Array.isArray(raw) ? raw : (raw?.items ?? []);
        setFiles(list.map((f: any) => ({ ...f, tags: Array.isArray(f?.tags) ? f.tags : [] })));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUploaded = async (created: any[]) => {
    try {
      setIsUpdating(true);
      console.log('📥 Files uploaded callback received:', created.length, 'files');
      
      const newFiles = created.map(doc => ({
        ...doc,
        tags: Array.isArray(doc.tags) ? doc.tags : []
      }));
      
      console.log('📁 Adding files to state:', newFiles);
      
      setFiles(prev => {
        const updated = [...newFiles, ...prev];
        console.log('📊 Files state updated. Total files:', updated.length);
        return updated;
      });
      
      if (selectedFolder) {
        console.log('📁 Updating folder files for:', selectedFolder.name);
        setFolders(prev => prev.map(folder => 
          folder.id === selectedFolder.id 
            ? { 
                ...folder, 
                files: [...newFiles, ...(folder.files || [])] 
              }
            : folder
        ));
      }
      
      console.log('✅ Files added to state successfully');
      
      setTimeout(() => {
        console.log('🔄 Refreshing page data...');
        fetchDataWithoutReset().finally(() => {
          setIsUpdating(false);
        });
      }, 200);
      
    } catch (error) {
      console.error('💥 Error handling upload callback:', error);
      setIsUpdating(false);
    }
  };

  const handleSelectFolder = (folder: DocumentFolder) => {
    setSelectedFolder(folder);
    const params = new URLSearchParams(searchParams);
    params.set('folder', folder.id);
    router.push(`/document?${params.toString()}`, { scroll: false });
  };

  const handleGoBack = () => {
    setSelectedFolder(null);
    router.push('/document', { scroll: false });
  };

  const handleCloseModal = () => {
    console.log('🚪 Modal closed by user');
    setShowFileUpload(false);
    
    setTimeout(() => {
      fetchDataWithoutReset();
    }, 100);
  };

  const fetchDataWithoutReset = async () => {
    try {
      const [foldersRes, filesRes] = await Promise.all([
        fetch('/api/folder', { cache: 'no-store' }),
        fetch('/api/document', { cache: 'no-store' }),
      ]);

      if (foldersRes.ok) {
        const foldersData = await foldersRes.json();
        setFolders(foldersData);
        
        if (selectedFolder) {
          const updatedFolder = foldersData.find((f: DocumentFolder) => f.id === selectedFolder.id);
          if (updatedFolder) {
            setSelectedFolder(updatedFolder);
          }
        }
      }

      if (filesRes.ok) {
        const raw = await filesRes.json();
        const list = Array.isArray(raw) ? raw : (raw?.items ?? []);
        setFiles(list.map((f: any) => ({ ...f, tags: Array.isArray(f?.tags) ? f.tags : [] })));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const createFolder = async () => {
    try {
      const response = await fetch('/api/folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: folderName, 
          color: folderColor 
        }),
      });
      
      if (response.ok) {
        await fetchDataWithoutReset();
        setShowCreateFolder(false);
        setFolderName('');
        setFolderColor('#3B82F6');
      }
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };

  const updateFolderColor = async (folderId: string, newColor: string) => {
    try {
      const response = await fetch(`/api/folder/${folderId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ color: newColor }),
      });
      
      if (response.ok) {
        await fetchDataWithoutReset();
        setShowColorPicker(null);
      }
    } catch (error) {
      console.error('Error updating folder color:', error);
    }
  };

  // ⭐ เพิ่มฟังก์ชันลบโฟลเดอร์
  const deleteFolder = async (folderId: string) => {
    try {
      const response = await fetch(`/api/folder/${folderId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log(`🗑️ Folder deleted successfully. ${result.deletedFiles || 0} files also deleted.`);
        
        // ลบโฟลเดอร์ออกจาก state
        setFolders(prev => prev.filter(folder => folder.id !== folderId));
        
        // ลบไฟล์ที่อยู่ในโฟลเดอร์ออกจาก state
        setFiles(prev => prev.filter(file => file.folderId !== folderId));
        
        // ถ้าอยู่ในโฟลเดอร์ที่ถูกลบ ให้กลับไปหน้าหลัก
        if (selectedFolder?.id === folderId) {
          handleGoBack();
        }
        
        setShowDeleteFolderConfirm(null);
      } else {
        console.error('Failed to delete folder');
      }
    } catch (error) {
      console.error('Error deleting folder:', error);
    }
  };

  const deleteFile = async (fileId: string) => {
    try {
      const response = await fetch(`/api/document/${fileId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setFiles(prev => prev.filter(file => file.id !== fileId));
        setShowDeleteConfirm(null);
      }
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  const getRecentActivity = () => {
    const allItems = [
      ...folders.map(f => ({ ...f, itemType: 'folder', time: f.updatedAt })),
      ...files.map(f => ({ ...f, itemType: 'file', time: f.updatedAt }))
    ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 5);
    
    return allItems;
  };

  const visibleFolders = folders.filter(folder =>
    folder.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const visibleFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (file.tags ?? []).some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    if (selectedFolder) {
      return matchesSearch && file.folderId === selectedFolder.id;
    } else {
      return matchesSearch && !file.folderId;
    }
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">กำลังโหลดเอกสารของคุณ...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="flex">
        {/* Main Content */}
        <div className="flex-1 p-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                {/* Breadcrumb */}
                <div className="flex items-center space-x-2 mb-3">
                  <button
                    onClick={handleGoHome}
                    className="flex items-center space-x-2 text-gray-500 hover:text-blue-600 transition-colors duration-200 group"
                  >
                    <Home className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    <span className="text-sm font-medium">หน้าแรก</span>
                  </button>
                  <span className="text-gray-300">›</span>
                  <span className="text-sm font-medium text-gray-900">เอกสารภาษี</span>
                  {selectedFolder && (
                    <>
                      <span className="text-gray-300">›</span>
                      <span className="text-sm font-medium text-blue-600">{selectedFolder.name}</span>
                    </>
                  )}
                </div>

                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <FileText className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                      {selectedFolder ? selectedFolder.name : 'เอกสารภาษี'}
                    </h1>
                    <p className="text-gray-500 mt-1">
                      {selectedFolder 
                        ? `${visibleFiles.length} ไฟล์ในโฟลเดอร์นี้`
                        : 'จัดการไฟล์และโฟลเดอร์เอกสารภาษีของคุณ'
                      }
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                {selectedFolder && (
                  <>
                    <button
                      onClick={handleGoBack}
                      className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-all duration-200 flex items-center space-x-2"
                    >
                      <Home className="w-5 h-5" />
                      <span>กลับหน้าหลัก</span>
                    </button>
                    
                    {/* ⭐ เพิ่มปุ่มลบโฟลเดอร์ */}
                    <button
                      onClick={() => setShowDeleteFolderConfirm(selectedFolder.id)}
                      className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-all duration-200 flex items-center space-x-2"
                    >
                      <Trash2 className="w-5 h-5" />
                      <span>ลบโฟลเดอร์</span>
                    </button>
                  </>
                )}
                
                <button
                  onClick={() => setShowCreateFolder(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-all duration-200 flex items-center space-x-2"
                >
                  <FolderPlus className="w-5 h-5" />
                  <span>สร้างโฟลเดอร์</span>
                </button>

                <button
                  onClick={() => setShowFileUpload(true)}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-all duration-200 flex items-center space-x-2"
                >
                  <Upload className="w-5 h-5" />
                  <span>อัปโหลดไฟล์</span>
                </button>
              </div>
            </div>

            {/* Search and Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="relative group">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
                  <input
                    type="text"
                    placeholder="ค้นหาเอกสารและโฟลเดอร์..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-96 pl-12 pr-6 py-3 bg-white border border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 shadow-sm hover:shadow-md transition-all duration-300"
                  />
                </div>
                
                <button className="p-3 text-gray-500 hover:text-gray-700 hover:bg-white hover:shadow-md rounded-2xl transition-all duration-300">
                  <Filter className="w-5 h-5" />
                </button>
                
                <button className="p-3 text-gray-500 hover:text-gray-700 hover:bg-white hover:shadow-md rounded-2xl transition-all duration-300">
                  <SortAsc className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex items-center space-x-2 bg-white rounded-2xl p-1 shadow-sm">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-xl transition-all duration-300 ${
                    viewMode === 'grid' 
                      ? 'bg-blue-500 text-white shadow-md' 
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Grid3X3 className="w-5 h-5" />
                </button>
                
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-xl transition-all duration-300 ${
                    viewMode === 'list' 
                      ? 'bg-blue-500 text-white shadow-md' 
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Content Grid */}
          <div className={`grid gap-6 ${
            viewMode === 'grid' 
              ? 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4' 
              : 'grid-cols-1'
          }`}>
            {/* Folders */}
            {!selectedFolder && visibleFolders.map((folder) => (
              <div
                key={folder.id}
                className="group relative transform hover:scale-105 transition-all duration-300"
              >
                <div
                  className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 cursor-pointer overflow-hidden"
                  style={{
                    background: `linear-gradient(135deg, ${folder.color}08, ${folder.color}15)`,
                    borderLeft: `6px solid ${folder.color}`,
                  }}
                  onClick={() => handleSelectFolder(folder)}
                >
                  <div className="absolute top-0 right-0 w-20 h-20 opacity-5"
                       style={{ backgroundColor: folder.color }}></div>
                  
                  <div className="flex items-center justify-between mb-4">
                    <div 
                      className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-md transform group-hover:rotate-12 transition-transform duration-300"
                      style={{ backgroundColor: `${folder.color}20` }}
                    >
                      <Folder 
                        className="w-7 h-7"
                        style={{ color: folder.color }}
                      />
                    </div>
                    
                    <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 flex space-x-1">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowColorPicker(showColorPicker === folder.id ? null : folder.id);
                        }}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white hover:shadow-md rounded-xl transition-all duration-300"
                      >
                        <Palette className="w-4 h-4" />
                      </button>
                      
                      {/* ⭐ เพิ่มปุ่มลบโฟลเดอร์ในการ์ด */}
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteFolderConfirm(folder.id);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 hover:shadow-md rounded-xl transition-all duration-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <h3 className="font-bold text-gray-800 mb-2 text-lg truncate">
                    {folder.name}
                  </h3>
                  
                  <div className="flex items-center justify-between">
                    <p className="text-gray-500 font-medium">
                      {files.filter(file => file.folderId === folder.id).length} ไฟล์
                    </p>
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: folder.color }}></div>
                  </div>
                  
                  {showColorPicker === folder.id && (
                    <div className="absolute top-0 right-0 mt-16 mr-4 bg-white rounded-2xl shadow-2xl border p-4 z-20 transform scale-0 group-hover:scale-100 transition-transform duration-300">
                      <p className="text-sm font-medium text-gray-700 mb-3">เลือกสี</p>
                      <div className="grid grid-cols-3 gap-3">
                        {predefinedColors.map((color) => (
                          <button
                            key={color}
                            onClick={(e) => {
                              e.stopPropagation();
                              updateFolderColor(folder.id, color);
                            }}
                            className="w-8 h-8 rounded-2xl border-2 border-gray-200 hover:scale-125 hover:shadow-lg transition-all duration-300 transform"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Files */}
            {visibleFiles.map((file) => (
              <div
                key={file.id}
                className="group relative transform hover:scale-105 transition-all duration-300"
              >
                <div
                  className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 cursor-pointer"
                  onClick={() => router.push(`/document/${file.id}`)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-14 h-14 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center shadow-md transform group-hover:rotate-12 transition-transform duration-300">
                      <FileText className="w-7 h-7 text-gray-600" />
                    </div>
                    
                    <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 flex space-x-2">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm(file.id);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 hover:shadow-md rounded-xl transition-all duration-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 hover:shadow-md rounded-xl transition-all duration-300">
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <h3 className="font-bold text-gray-800 mb-3 text-lg truncate">
                    {file.name}
                  </h3>
                  
                  <div className="flex flex-wrap gap-2 mb-3">
                    {(file.tags || []).slice(0, 2).map((tag) => (
                      <span 
                        key={tag}
                        className="px-3 py-1 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 text-xs font-medium rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {(file.tags || []).length > 2 && (
                      <span className="px-3 py-1 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-600 text-xs font-medium rounded-full">
                        +{file.tags.length - 2}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-gray-500 font-medium">
                    {file.type?.replace('_', ' ') || 'Document'}
                  </p>
                </div>
              </div>
            ))}

            {/* Empty States */}
            {!selectedFolder && visibleFolders.length === 0 && visibleFiles.length === 0 && (
              <div className="col-span-full text-center py-16">
                <div className="w-20 h-20 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-6">
                  <FileText className="w-10 h-10 text-gray-500" />
                </div>
                <h3 className="text-xl font-bold text-gray-700 mb-2">ยังไม่มีเอกสาร</h3>
                <p className="text-gray-500 mb-6">เริ่มต้นด้วยการสร้างโฟลเดอร์หรืออัปโหลดไฟล์</p>
                <div className="flex justify-center space-x-4">
                  <button
                    onClick={() => setShowCreateFolder(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
                  >
                    สร้างโฟลเดอร์แรก
                  </button>
                  <button
                    onClick={() => setShowFileUpload(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-medium"
                  >
                    อัปโหลดไฟล์แรก
                  </button>
                </div>
              </div>
            )}

            {selectedFolder && visibleFiles.length === 0 && (
              <div className="col-span-full text-center py-16">
                <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6"
                     style={{ backgroundColor: `${selectedFolder.color}20` }}>
                  <Folder className="w-10 h-10" style={{ color: selectedFolder.color }} />
                </div>
                <h3 className="text-xl font-bold text-gray-700 mb-2">โฟลเดอร์ว่าง</h3>
                <p className="text-gray-500 mb-6">อัปโหลดไฟล์เอกสารลงในโฟลเดอร์นี้</p>
                <button
                  onClick={() => setShowFileUpload(true)}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-medium"
                >
                  อัปโหลดไฟล์
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-96 bg-white border-l border-gray-200 p-8 backdrop-blur-sm bg-white/90">
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">รายละเอียด</h2>
          </div>
          
          {/* Color Picker Section */}
          <div className="mb-8 p-6 bg-gradient-to-br from-orange-50 to-pink-50 rounded-3xl">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center space-x-2">
              <Palette className="w-5 h-5" />
              <span>เลือกสี</span>
            </h3>
            <div className="bg-gradient-to-r from-orange-400 via-red-400 to-purple-600 h-10 rounded-2xl mb-3 shadow-md"></div>
            <p className="text-sm text-gray-600 font-medium">#b075883</p>
          </div>
          
          {/* Recent Activity */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center space-x-2">
              <Clock className="w-5 h-5" />
              <span>กิจกรรมล่าสุด</span>
            </h3>
            <div className="space-y-4">
              {getRecentActivity().map((item, index) => (
                <div key={index} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors duration-300">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-md">
                    <Clock className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-800 font-medium text-sm">
                      {(item as any).itemType === 'folder' ? 'สร้างโฟลเดอร์' : 'อัพโหลดไฟล์'}: 
                      <span className="font-bold ml-1">{item.name}</span>
                    </p>
                    <p className="text-gray-500 text-xs mt-1">
                      {new Date(item.time).toLocaleDateString('th-TH')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Tags */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center space-x-2">
              <Tag className="w-5 h-5" />
              <span>แท็ก</span>
            </h3>
            <div className="flex flex-wrap gap-3">
              {commonTags.slice(0, 2).map((tag) => (
                <span 
                  key={tag}
                  className="px-4 py-2 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 font-medium rounded-full cursor-pointer hover:from-blue-200 hover:to-indigo-200 transition-all duration-300 transform hover:scale-105"
                >
                  {tag}
                </span>
              ))}
              <button className="px-4 py-2 text-gray-500 border-2 border-dashed border-gray-300 rounded-full hover:border-gray-400 hover:text-gray-600 transition-all duration-300">
                •••
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Loading Indicator */}
      {isUpdating && (
        <div className="fixed top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          <div className="flex items-center space-x-2">
            <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
            <span>กำลังอัพเดท...</span>
          </div>
        </div>
      )}

      {/* Create Folder Modal */}
      {showCreateFolder && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-3xl p-8 w-96 max-w-lg shadow-2xl border transform scale-110">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                <FolderPlus className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">สร้างโฟลเดอร์ใหม่</h3>
              <p className="text-gray-500">จัดระเบียบเอกสารของคุณ</p>
            </div>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-3">
                  ชื่อโฟลเดอร์
                </label>
                <input
                  type="text"
                  value={folderName}
                  onChange={(e) => setFolderName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-300"
                  placeholder="ใส่ชื่อโฟลเดอร์..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-3">
                  เลือกสี
                </label>
                <div className="grid grid-cols-5 gap-3">
                  {predefinedColors.map((color) => (
                    <button
                      key={color}
                      onClick={() => setFolderColor(color)}
                      className={`w-10 h-10 rounded-2xl border-2 transition-all duration-300 transform hover:scale-110 ${
                        folderColor === color 
                          ? 'border-gray-800 scale-110 shadow-lg' 
                          : 'border-gray-200 hover:shadow-md'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-center space-x-4 mt-8">
              <button
                onClick={() => setShowCreateFolder(false)}
                className="px-6 py-3 text-gray-600 hover:text-gray-800 font-medium rounded-2xl hover:bg-gray-100 transition-all duration-300"
              >
                ยกเลิก
              </button>
              <button
                onClick={createFolder}
                disabled={!folderName.trim()}
                className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold rounded-2xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
              >
                สร้างโฟลเดอร์
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ⭐ Delete Folder Confirmation Modal */}
      {showDeleteFolderConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-96 max-w-lg shadow-xl">
            <div className="flex items-center space-x-4 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">ลบโฟลเดอร์</h3>
                <p className="text-sm text-gray-600">การดำเนินการนี้ไม่สามารถยกเลิกได้</p>
              </div>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-red-800">
                    โฟลเดอร์และไฟล์ทั้งหมดภายในจะถูกลบถาวร
                  </p>
                  <p className="text-xs text-red-600 mt-1">
                    {(() => {
                      const folder = folders.find(f => f.id === showDeleteFolderConfirm);
                      const fileCount = files.filter(file => file.folderId === showDeleteFolderConfirm).length;
                      return `โฟลเดอร์ "${folder?.name}" มีไฟล์ ${fileCount} ไฟล์`;
                    })()}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteFolderConfirm(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium rounded-lg hover:bg-gray-100 transition-all duration-200"
              >
                ยกเลิก
              </button>
              <button
                onClick={() => deleteFolder(showDeleteFolderConfirm)}
                className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-all duration-200"
              >
                ลบโฟลเดอร์
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete File Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-96 max-w-lg shadow-xl">
            <div className="flex items-center space-x-4 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">ลบไฟล์</h3>
                <p className="text-sm text-gray-600">คุณแน่ใจที่จะลบไฟล์นี้หรือไม่?</p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium rounded-lg hover:bg-gray-100 transition-all duration-200"
              >
                ยกเลิก
              </button>
              <button
                onClick={() => deleteFile(showDeleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-all duration-200"
              >
                ลบ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={showFileUpload}
        onClose={handleCloseModal}
        onUploaded={handleUploaded}
        folderId={selectedFolder?.id}
      />
    </div>
  );
}