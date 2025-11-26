'use client';

import React, { useState, useEffect } from 'react';
import { useRouter , useSearchParams} from 'next/navigation';
import { useSession } from 'next-auth/react';
import { AppNavigation } from '@/components/AppNavigation';
import FileUploadModal from '@/components/FileUploadModal/FileUploadModal';
import RenameModal from '@/components/RenameModal';
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
  AlertTriangle,
  Pencil,
  Download,
  Copy,
  Move,
  Info,
  FileImage,
  FileSpreadsheet,
  File,
} from 'lucide-react';

interface DocumentFolder {
  id: string;
  name: string;
  color: string;
  parentId: string | null;
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
  const [renameItem, setRenameItem] = useState<{ id: string; name: string; type: 'file' | 'folder' } | null>(null);
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Form states
  const [folderName, setFolderName] = useState('');
  const [folderColor, setFolderColor] = useState('#3B82F6');

  // Filter & Sort states
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'size'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Breadcrumb path for nested folders
  const [folderPath, setFolderPath] = useState<DocumentFolder[]>([]);

  const handleGoHome = () => {
    router.push('/WelcomeHome');
  };

  // Fetch data
  useEffect(() => {
    fetchData();
  }, []);

  // Close dropdown menus when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowMoreMenu(null);
      setShowFilterMenu(false);
      setShowSortMenu(false);
    };

    if (showMoreMenu || showFilterMenu || showSortMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showMoreMenu, showFilterMenu, showSortMenu]);

  useEffect(() => {
    const folderId = searchParams.get('folder');
    if (folderId && folders.length > 0) {
      const folder = folders.find(f => f.id === folderId);
      if (folder) {
        setSelectedFolder(folder);
        // สร้าง breadcrumb path
        buildFolderPath(folder);
      }
    } else {
      setSelectedFolder(null);
      setFolderPath([]);
    }
  }, [searchParams, folders]);

  // สร้าง breadcrumb path โดยย้อนกลับไปหา parent folders
  const buildFolderPath = (folder: DocumentFolder) => {
    const path: DocumentFolder[] = [folder];
    let currentFolder = folder;

    // ย้อนกลับไปหา parent folders
    while (currentFolder.parentId) {
      const parent = folders.find(f => f.id === currentFolder.parentId);
      if (parent) {
        path.unshift(parent);
        currentFolder = parent;
      } else {
        break;
      }
    }

    setFolderPath(path);
  };

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

      const newFiles = created.map(doc => ({
        ...doc,
        tags: Array.isArray(doc.tags) ? doc.tags : []
      }));

      setFiles(prev => {
        const updated = [...newFiles, ...prev];
        return updated;
      });

      if (selectedFolder) {
        setFolders(prev => prev.map(folder =>
          folder.id === selectedFolder.id
            ? {
                ...folder,
                files: [...newFiles, ...(folder.files || [])]
              }
            : folder
        ));
      }

      setTimeout(() => {
        fetchDataWithoutReset().finally(() => {
          setIsUpdating(false);
        });
      }, 200);

    } catch (error) {
      console.error('Error handling upload callback:', error);
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
    if (selectedFolder?.parentId) {
      // ถ้ามี parent folder ให้กลับไปที่ parent
      const params = new URLSearchParams();
      params.set('folder', selectedFolder.parentId);
      router.push(`/document?${params.toString()}`, { scroll: false });
    } else {
      // ถ้าไม่มี parent (root folder) ให้กลับไปหน้าหลัก
      setSelectedFolder(null);
      router.push('/document', { scroll: false });
    }
  };

  const handleCloseModal = () => {
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
          color: folderColor,
          parentId: selectedFolder?.id || null // ⭐ เพิ่ม parentId เพื่อสร้างโฟลเดอร์ซ้อน
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

  // More Options Actions
  const handleDownloadFile = async (file: DocumentFile) => {
    if (!file.fileUrl) return;

    try {
      // Fetch signed URL with download mode
      const response = await fetch(`/api/document/${file.id}/signed-url?download=true`);
      if (response.ok) {
        const data = await response.json();
        const link = document.createElement('a');
        link.href = data.url;
        link.download = file.fileName || file.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error('Error downloading file:', error);
    }
    setShowMoreMenu(null);
  };

  const handleCopyLink = (fileId: string) => {
    const link = `${window.location.origin}/document/${fileId}`;
    navigator.clipboard.writeText(link);
    setToastMessage('คัดลอกลิงก์แล้ว');
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
    setShowMoreMenu(null);
  };

  const handleViewDetails = (fileId: string) => {
    router.push(`/document/${fileId}`);
    setShowMoreMenu(null);
  };

  // Helper function to get file icon
  const getFileIcon = (file: DocumentFile) => {
    const mimeType = file.mimeType || '';
    const fileName = file.fileName || file.name || '';
    const extension = fileName.split('.').pop()?.toLowerCase();

    if (mimeType.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(extension || '')) {
      return <FileImage className="w-7 h-7 text-green-600" />;
    } else if (mimeType.includes('pdf') || extension === 'pdf') {
      return <FileText className="w-7 h-7 text-red-600" />;
    } else if (mimeType.includes('sheet') || mimeType.includes('excel') || ['xlsx', 'xls', 'csv'].includes(extension || '')) {
      return <FileSpreadsheet className="w-7 h-7 text-green-700" />;
    } else if (mimeType.includes('word') || mimeType.includes('document') || ['docx', 'doc'].includes(extension || '')) {
      return <FileText className="w-7 h-7 text-blue-600" />;
    } else {
      return <File className="w-7 h-7 text-gray-600" />;
    }
  };

  // Filter and Sort logic - แสดงเฉพาะ folders ในระดับปัจจุบัน
  const visibleFolders = folders
    .filter(folder => {
      // แสดงเฉพาะ folders ที่มี parentId ตรงกับ folder ปัจจุบัน
      const isInCurrentLevel = selectedFolder
        ? folder.parentId === selectedFolder.id
        : !folder.parentId; // ถ้าไม่ได้เลือก folder ให้แสดง root folders (ที่ไม่มี parent)

      const matchesSearch = folder.name.toLowerCase().includes(searchQuery.toLowerCase());

      return isInCurrentLevel && matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return sortOrder === 'asc'
          ? a.name.localeCompare(b.name, 'th')
          : b.name.localeCompare(a.name, 'th');
      } else if (sortBy === 'date') {
        const dateA = new Date(a.updatedAt).getTime();
        const dateB = new Date(b.updatedAt).getTime();
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
      }
      return 0;
    });

  const visibleFiles = files
    .filter(file => {
      const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (file.tags ?? []).some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesType = filterType === 'all' || file.type === filterType;

      if (selectedFolder) {
        return matchesSearch && matchesType && file.folderId === selectedFolder.id;
      } else {
        return matchesSearch && matchesType && !file.folderId;
      }
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return sortOrder === 'asc'
          ? a.name.localeCompare(b.name, 'th')
          : b.name.localeCompare(a.name, 'th');
      } else if (sortBy === 'date') {
        const dateA = new Date(a.updatedAt).getTime();
        const dateB = new Date(b.updatedAt).getTime();
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
      } else if (sortBy === 'size') {
        const sizeA = a.fileSize || 0;
        const sizeB = b.fileSize || 0;
        return sortOrder === 'asc' ? sizeA - sizeB : sizeB - sizeA;
      }
      return 0;
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
    <div className="min-h-screen bg-gray-50">
      <AppNavigation />

      <div className="bg-gradient-to-br from-gray-50 to-blue-50 min-h-screen">
        <div className="flex">
          {/* Main Content */}
          <div className="flex-1 p-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                {/* Breadcrumb - Enhanced with nested folders */}
                <div className="flex items-center space-x-2 mb-3 flex-wrap">
                  <button
                    onClick={handleGoHome}
                    className="flex items-center space-x-2 text-gray-500 hover:text-blue-600 transition-colors duration-200 group"
                  >
                    <Home className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    <span className="text-sm font-medium">หน้าแรก</span>
                  </button>
                  <span className="text-gray-300">›</span>
                  <button
                    onClick={() => router.push('/document')}
                    className={`text-sm font-medium transition-colors duration-200 ${
                      !selectedFolder ? 'text-gray-900' : 'text-gray-500 hover:text-blue-600'
                    }`}
                  >
                    เอกสารภาษี
                  </button>

                  {/* แสดง breadcrumb path สำหรับ nested folders */}
                  {folderPath.map((folder, index) => (
                    <div key={folder.id} className="flex items-center space-x-2">
                      <span className="text-gray-300">›</span>
                      <button
                        onClick={() => {
                          const params = new URLSearchParams();
                          params.set('folder', folder.id);
                          router.push(`/document?${params.toString()}`, { scroll: false });
                        }}
                        className={`text-sm font-medium transition-colors duration-200 ${
                          index === folderPath.length - 1
                            ? 'text-blue-600'
                            : 'text-gray-500 hover:text-blue-600'
                        }`}
                        style={index === folderPath.length - 1 ? { color: folder.color } : {}}
                      >
                        {folder.name}
                      </button>
                    </div>
                  ))}
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
                        ? `${visibleFolders.length} โฟลเดอร์ • ${visibleFiles.length} ไฟล์`
                        : 'จัดการไฟล์และโฟลเดอร์เอกสารภาษีของคุณ'
                      }
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-3 flex-wrap">
                {selectedFolder ? (
                  <>
                    <button
                      onClick={handleGoBack}
                      className="group relative px-5 py-2.5 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white rounded-full font-medium shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 hover:scale-105"
                    >
                      <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
                        <Home className="w-4 h-4" />
                      </div>
                      <span>กลับหน้าหลัก</span>
                    </button>

                    {/* ⭐ เพิ่มปุ่มลบโฟลเดอร์ */}
                    <button
                      onClick={() => setShowDeleteFolderConfirm(selectedFolder.id)}
                      className="group relative px-5 py-2.5 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-full font-medium shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 hover:scale-105"
                    >
                      <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </div>
                      <span>ลบโฟลเดอร์</span>
                    </button>
                  </>
                ) : (
                  <>
                    {/* Trash Button - Only show on main page */}
                    <button
                      onClick={() => router.push('/trash')}
                      className="group relative px-5 py-2.5 bg-gradient-to-r from-slate-500 to-slate-600 hover:from-slate-600 hover:to-slate-700 text-white rounded-full font-medium shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 hover:scale-105"
                      title="ถังขยะ"
                    >
                      <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </div>
                      <span>ถังขยะ</span>
                    </button>
                  </>
                )}

                <button
                  onClick={() => setShowCreateFolder(true)}
                  className="group relative px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-full font-medium shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 hover:scale-105"
                >
                  <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
                    <FolderPlus className="w-4 h-4" />
                  </div>
                  <span>สร้างโฟลเดอร์</span>
                </button>

                <button
                  onClick={() => setShowFileUpload(true)}
                  className="group relative px-5 py-2.5 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-full font-medium shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2 hover:scale-105"
                >
                  <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
                    <Upload className="w-4 h-4" />
                  </div>
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

                {/* Filter Button */}
                <div className="relative">
                  <button
                    onClick={() => {
                      setShowFilterMenu(!showFilterMenu);
                      setShowSortMenu(false);
                    }}
                    className={`p-3 rounded-2xl transition-all duration-300 ${
                      showFilterMenu || filterType !== 'all'
                        ? 'bg-blue-500 text-white shadow-md'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-white hover:shadow-md'
                    }`}
                  >
                    <Filter className="w-5 h-5" />
                  </button>

                  {/* Filter Dropdown */}
                  {showFilterMenu && (
                    <div className="absolute top-14 right-0 bg-white rounded-2xl shadow-2xl border border-gray-200 p-4 z-20 w-64">
                      <h3 className="font-bold text-gray-800 mb-3">กรองตามประเภท</h3>
                      <div className="space-y-2">
                        {[
                          { value: 'all', label: 'ทั้งหมด' },
                          { value: 'TAX_FORM', label: 'แบบฟอร์มภาษี' },
                          { value: 'RECEIPT', label: 'ใบเสร็จ' },
                          { value: 'CONTRACT', label: 'สัญญา' },
                          { value: 'INVOICE', label: 'ใบแจ้งหนี้' },
                          { value: 'OTHER', label: 'อื่นๆ' },
                        ].map((option) => (
                          <button
                            key={option.value}
                            onClick={() => {
                              setFilterType(option.value);
                              setShowFilterMenu(false);
                            }}
                            className={`w-full text-left px-4 py-2 rounded-xl transition-all duration-200 ${
                              filterType === option.value
                                ? 'bg-blue-100 text-blue-700 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                            }`}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Sort Button */}
                <div className="relative">
                  <button
                    onClick={() => {
                      setShowSortMenu(!showSortMenu);
                      setShowFilterMenu(false);
                    }}
                    className={`p-3 rounded-2xl transition-all duration-300 ${
                      showSortMenu
                        ? 'bg-blue-500 text-white shadow-md'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-white hover:shadow-md'
                    }`}
                  >
                    <SortAsc className="w-5 h-5" />
                  </button>

                  {/* Sort Dropdown */}
                  {showSortMenu && (
                    <div className="absolute top-14 right-0 bg-white rounded-2xl shadow-2xl border border-gray-200 p-4 z-20 w-64">
                      <h3 className="font-bold text-gray-800 mb-3">เรียงตาม</h3>
                      <div className="space-y-2 mb-4">
                        {[
                          { value: 'date', label: 'วันที่' },
                          { value: 'name', label: 'ชื่อ' },
                          { value: 'size', label: 'ขนาด' },
                        ].map((option) => (
                          <button
                            key={option.value}
                            onClick={() => setSortBy(option.value as 'name' | 'date' | 'size')}
                            className={`w-full text-left px-4 py-2 rounded-xl transition-all duration-200 ${
                              sortBy === option.value
                                ? 'bg-blue-100 text-blue-700 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                            }`}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>

                      <h3 className="font-bold text-gray-800 mb-3">ลำดับ</h3>
                      <div className="space-y-2">
                        <button
                          onClick={() => {
                            setSortOrder('asc');
                            setShowSortMenu(false);
                          }}
                          className={`w-full text-left px-4 py-2 rounded-xl transition-all duration-200 ${
                            sortOrder === 'asc'
                              ? 'bg-blue-100 text-blue-700 font-medium'
                              : 'hover:bg-gray-100 text-gray-700'
                          }`}
                        >
                          น้อยไปมาก (A-Z, เก่า-ใหม่)
                        </button>
                        <button
                          onClick={() => {
                            setSortOrder('desc');
                            setShowSortMenu(false);
                          }}
                          className={`w-full text-left px-4 py-2 rounded-xl transition-all duration-200 ${
                            sortOrder === 'desc'
                              ? 'bg-blue-100 text-blue-700 font-medium'
                              : 'hover:bg-gray-100 text-gray-700'
                          }`}
                        >
                          มากไปน้อย (Z-A, ใหม่-เก่า)
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-1 bg-white/80 backdrop-blur-sm rounded-full p-1.5 shadow-lg border border-gray-200/50">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2.5 rounded-full transition-all duration-300 ${
                    viewMode === 'grid'
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md scale-105'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                  title="มุมมองตาราง"
                >
                  <Grid3X3 className="w-4 h-4" />
                </button>

                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2.5 rounded-full transition-all duration-300 ${
                    viewMode === 'list'
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md scale-105'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                  title="มุมมองรายการ"
                >
                  <List className="w-4 h-4" />
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
            {visibleFolders.map((folder) => (
              <div
                key={folder.id}
                className="group relative transform hover:scale-105 transition-all duration-300"
              >
                <div
                  className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 cursor-pointer"
                  style={{
                    background: `linear-gradient(135deg, ${folder.color}08, ${folder.color}15)`,
                    borderLeft: `6px solid ${folder.color}`,
                  }}
                  onClick={() => handleSelectFolder(folder)}
                >
                  <div className="absolute top-0 right-0 w-20 h-20 opacity-5 pointer-events-none"
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

                    <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 flex space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowColorPicker(showColorPicker === folder.id ? null : folder.id);
                        }}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white hover:shadow-md rounded-xl transition-all duration-300"
                        title="เปลี่ยนสีโฟลเดอร์"
                      >
                        <Palette className="w-4 h-4" />
                      </button>

                      {/* ⭐ เพิ่มปุ่มเปลี่ยนชื่อโฟลเดอร์ */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRenameItem({ id: folder.id, name: folder.name, type: 'folder' });
                        }}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 hover:shadow-md rounded-xl transition-all duration-300"
                        title="เปลี่ยนชื่อโฟลเดอร์"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>

                      {/* ⭐ เพิ่มปุ่มลบโฟลเดอร์ในการ์ด */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteFolderConfirm(folder.id);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 hover:shadow-md rounded-xl transition-all duration-300"
                        title="ลบโฟลเดอร์"
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
                    <div
                      className="absolute top-16 right-0 bg-white rounded-2xl shadow-2xl border border-gray-200 p-4 z-30"
                      onClick={(e) => e.stopPropagation()}
                    >
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
                      {getFileIcon(file)}
                    </div>

                    <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 flex space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRenameItem({ id: file.id, name: file.name, type: 'file' });
                        }}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 hover:shadow-md rounded-xl transition-all duration-300"
                        title="เปลี่ยนชื่อ"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm(file.id);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 hover:shadow-md rounded-xl transition-all duration-300"
                        title="ลบ"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>

                      {/* More Options Button */}
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowMoreMenu(showMoreMenu === file.id ? null : file.id);
                          }}
                          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 hover:shadow-md rounded-xl transition-all duration-300"
                          title="ตัวเลือกเพิ่มเติม"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </button>

                        {/* Dropdown Menu */}
                        {showMoreMenu === file.id && (
                          <div
                            className="absolute top-12 right-0 bg-white rounded-2xl shadow-2xl border border-gray-200 p-2 z-30 w-56"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDownloadFile(file);
                              }}
                              className="w-full text-left px-4 py-2 rounded-xl hover:bg-gray-100 text-gray-700 flex items-center space-x-3 transition-colors"
                            >
                              <Download className="w-4 h-4" />
                              <span>ดาวน์โหลด</span>
                            </button>

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopyLink(file.id);
                              }}
                              className="w-full text-left px-4 py-2 rounded-xl hover:bg-gray-100 text-gray-700 flex items-center space-x-3 transition-colors"
                            >
                              <Copy className="w-4 h-4" />
                              <span>คัดลอกลิงก์</span>
                            </button>

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewDetails(file.id);
                              }}
                              className="w-full text-left px-4 py-2 rounded-xl hover:bg-gray-100 text-gray-700 flex items-center space-x-3 transition-colors"
                            >
                              <Info className="w-4 h-4" />
                              <span>ดูรายละเอียด</span>
                            </button>

                            <hr className="my-2 border-gray-200" />

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setRenameItem({ id: file.id, name: file.name, type: 'file' });
                                setShowMoreMenu(null);
                              }}
                              className="w-full text-left px-4 py-2 rounded-xl hover:bg-blue-50 text-blue-600 flex items-center space-x-3 transition-colors"
                            >
                              <Pencil className="w-4 h-4" />
                              <span>เปลี่ยนชื่อ</span>
                            </button>

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setShowDeleteConfirm(file.id);
                                setShowMoreMenu(null);
                              }}
                              className="w-full text-left px-4 py-2 rounded-xl hover:bg-red-50 text-red-600 flex items-center space-x-3 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                              <span>ลบ</span>
                            </button>
                          </div>
                        )}
                      </div>
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
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {selectedFolder ? 'สร้างโฟลเดอร์ย่อย' : 'สร้างโฟลเดอร์ใหม่'}
              </h3>
              <p className="text-gray-500">
                {selectedFolder
                  ? `สร้างโฟลเดอร์ภายใน "${selectedFolder.name}"`
                  : 'จัดระเบียบเอกสารของคุณ'
                }
              </p>
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

      {/* Rename Modal */}
      {renameItem && (
        <RenameModal
          item={renameItem}
          onClose={() => setRenameItem(null)}
          onSuccess={() => {
            setRenameItem(null);
            fetchData(); // Refresh data after rename
          }}
        />
      )}

      {/* Toast Notification */}
      {showToast && (
        <div className="fixed bottom-6 right-6 bg-gradient-to-r from-green-600 to-green-500 text-white px-6 py-3 rounded-2xl shadow-2xl z-50 flex items-center space-x-3 animate-bounce">
          <div className="w-2 h-2 bg-white rounded-full"></div>
          <span className="font-medium">{toastMessage}</span>
        </div>
      )}
      </div>
    </div>
  );
}