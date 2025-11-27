'use client';

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import SafeImage from '@/components/SafeImage/SafeImage';

import { ArrowLeft, Download, Calendar, Tag, FileText, Loader2 } from 'lucide-react';
import Link from "next/link";

type DocumentFile = {
  id: string;
  name: string;
  fileName: string | null;
  fileUrl: string | null;
  mimeType: string | null;
  fileSize: number | null;
  type: string | null;
  tags: any;
  createdAt: string;
  updatedAt: string;
  folder: {
    id: string;
    name: string;
    color: string;
  } | null;
};

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { status } = useSession();

  const [documentId, setDocumentId] = useState<string>('');
  const [doc, setDoc] = useState<DocumentFile | null>(null);
  const [signedUrl, setSignedUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  // Unwrap params
  useEffect(() => {
    params.then(p => setDocumentId(p.id));
  }, [params]);

  useEffect(() => {
    if (!documentId) return;
    if (status === 'unauthenticated') {
      router.push('/login');
      return;
    }

    if (status !== 'authenticated') return;

    async function loadDocument() {
      try {
        setLoading(true);
        setError('');

        // 1️⃣ Fetch document data
        const docRes = await fetch(`/api/document/${documentId}`);
        if (!docRes.ok) {
          if (docRes.status === 404) {
            setError('ไม่พบเอกสาร');
            return;
          }
          throw new Error('Failed to load document');
        }

        const docData = await docRes.json();
        setDoc(docData);

        // 2️⃣ Fetch signed URL if file exists
        if (docData.fileUrl) {
          console.log('Fetching signed URL for:', docData.fileUrl);
          const urlRes = await fetch(`/api/document/${documentId}/signed-url`);
          if (urlRes.ok) {
            const urlData = await urlRes.json();
            console.log('✅ Signed URL received:', urlData.url.substring(0, 100) + '...');
            setSignedUrl(urlData.url);
          } else {
            const errorData = await urlRes.json();
            console.error('❌ Failed to get signed URL:', errorData);
            // Fallback to direct URL (for local files)
            setSignedUrl(docData.fileUrl);
          }
        }
      } catch (err: any) {
        console.error('Error loading document:', err);
        setError(err.message || 'เกิดข้อผิดพลาดในการโหลดเอกสาร');
      } finally {
        setLoading(false);
      }
    }

    loadDocument();
  }, [documentId, status, router]);

  // Loading state
  if (loading || status === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">กำลังโหลดเอกสาร...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !doc) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-red-100 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <FileText className="w-12 h-12 text-red-600" />
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">เกิดข้อผิดพลาด</h3>
          <p className="text-gray-600 mb-6">{error || 'ไม่พบเอกสาร'}</p>
          <Link
            href="/document"
            className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-2xl shadow-sm hover:shadow-md transition-all duration-200"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>กลับไปหน้าเอกสาร</span>
          </Link>
        </div>
      </div>
    );
  }

  // File type detection
  const mimeType = doc.mimeType || '';
  const fileName = doc.fileName || doc.name || '';
  const fileExtension = fileName.split('.').pop()?.toLowerCase() || '';

  const isImage = mimeType.startsWith("image/") ||
    ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(fileExtension);

  const isPdf = mimeType.includes("pdf") || fileExtension === 'pdf';
  const isVideo = mimeType.startsWith("video/") ||
    ['mp4', 'webm', 'ogg', 'avi', 'mov'].includes(fileExtension);
  const isAudio = mimeType.startsWith("audio/") ||
    ['mp3', 'wav', 'ogg', 'm4a', 'flac'].includes(fileExtension);
  const isText = mimeType.startsWith("text/") ||
    ['txt', 'md', 'csv'].includes(fileExtension);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <Link
                href={doc.folder ? `/document?folder=${doc.folder.id}` : '/document'}
                className="p-3 bg-white hover:bg-gray-50 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>

              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{doc.name}</h1>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(doc.createdAt).toLocaleDateString('th-TH', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}</span>
                  </div>

                  {doc.folder && (
                    <div className="flex items-center space-x-1">
                      <span>ใน</span>
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium"
                        style={{
                          backgroundColor: `${doc.folder.color}20`,
                          color: doc.folder.color
                        }}
                      >
                        {doc.folder.name}
                      </span>
                    </div>
                  )}

                  {doc.fileSize && (
                    <span>
                      {(doc.fileSize / 1024 / 1024).toFixed(2)} MB
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3">
              {signedUrl && (
                <a
                  href={signedUrl}
                  download={doc.fileName || doc.name}
                  className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-2xl shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <Download className="w-5 h-5" />
                  <span>ดาวน์โหลด</span>
                </a>
              )}
            </div>
          </div>

          {/* Tags */}
          {Array.isArray(doc.tags) && doc.tags.length > 0 && (
            <div className="flex items-center space-x-2 mb-6">
              <Tag className="w-5 h-5 text-gray-500" />
              <div className="flex flex-wrap gap-2">
                {doc.tags.map((tag: string) => (
                  <span
                    key={tag}
                    className="px-3 py-1 text-sm rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* File Preview */}
        <div className="bg-white rounded-3xl shadow-xl border border-gray-200 overflow-hidden">
          {signedUrl ? (
            <div className="p-6">
              {isImage ? (
                <div className="text-center">
                  <SafeImage
                    src={signedUrl}
                    alt={doc.name}
                    className="max-w-full max-h-[80vh] object-contain mx-auto rounded-2xl shadow-lg"
                  />
                </div>
              ) : isPdf ? (
                <div className="w-full">
                  <iframe
                    src={`${signedUrl}#toolbar=1`}
                    className="w-full h-[80vh] rounded-2xl border border-gray-200"
                    title={doc.name}
                  />
                </div>
              ) : isVideo ? (
                <div className="text-center">
                  <video
                    controls
                    className="max-w-full max-h-[80vh] mx-auto rounded-2xl shadow-lg"
                  >
                    <source src={signedUrl} type={mimeType || undefined} />
                    เบราว์เซอร์ของคุณไม่สนับสนุนการเล่นวิดีโอ
                  </video>
                </div>
              ) : isAudio ? (
                <div className="text-center py-20">
                  <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
                    <FileText className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">{doc.name}</h3>
                  <audio controls className="mx-auto">
                    <source src={signedUrl} type={mimeType || undefined} />
                    เบราว์เซอร์ของคุณไม่สนับสนุนการเล่นเสียง
                  </audio>
                </div>
              ) : isText ? (
                <div className="prose max-w-none">
                  <iframe
                    src={signedUrl}
                    className="w-full h-[60vh] border border-gray-200 rounded-2xl"
                    title={doc.name}
                  />
                </div>
              ) : (
                <div className="text-center py-20">
                  <div className="w-24 h-24 bg-gradient-to-br from-gray-400 to-gray-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
                    <FileText className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">
                    ไม่สามารถแสดงตัวอย่างไฟล์ได้
                  </h3>
                  <p className="text-gray-600 mb-2">
                    ไฟล์ประเภท {mimeType || fileExtension || "ไม่ทราบ"}
                  </p>
                  <p className="text-gray-600 mb-6">
                    ไม่สามารถแสดงตัวอย่างได้ กรุณาดาวน์โหลดเพื่อดูเนื้อหา
                  </p>
                  <a
                    href={signedUrl}
                    download={doc.fileName || doc.name}
                    className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-2xl shadow-sm hover:shadow-md transition-all duration-200"
                  >
                    <Download className="w-5 h-5" />
                    <span>ดาวน์โหลดไฟล์</span>
                  </a>
                </div>
              )}
            </div>
          ) : doc.fileUrl ? (
            <div className="p-20 text-center">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">กำลังโหลดไฟล์...</p>
            </div>
          ) : (
            <div className="p-20 text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-3xl flex items-center justify-center mx-auto mb-6">
                <FileText className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                ไม่พบไฟล์
              </h3>
              <p className="text-gray-600">
                เอกสารนี้ไม่มีไฟล์แนบ
              </p>
            </div>
          )}
        </div>

        {/* File Info */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">ข้อมูลไฟล์</h3>
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">ประเภท:</span>
                <p className="font-medium">{doc.type?.replace('_', ' ') || 'ไม่ระบุ'}</p>
              </div>
              {mimeType && (
                <div>
                  <span className="text-sm text-gray-500">MIME Type:</span>
                  <p className="font-medium text-sm">{mimeType}</p>
                </div>
              )}
              {doc.fileName && (
                <div>
                  <span className="text-sm text-gray-500">ชื่อไฟล์:</span>
                  <p className="font-medium text-sm">{doc.fileName}</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">วันที่</h3>
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">สร้าง:</span>
                <p className="font-medium">{new Date(doc.createdAt).toLocaleDateString('th-TH')}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">แก้ไขล่าสุด:</span>
                <p className="font-medium">{new Date(doc.updatedAt).toLocaleDateString('th-TH')}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">สถานะ</h3>
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">อัปโหลดแล้ว:</span>
                <p className="font-medium">
                  {doc.fileUrl ? (
                    <span className="text-green-600">✓ สำเร็จ</span>
                  ) : (
                    <span className="text-red-600">✗ ไม่สำเร็จ</span>
                  )}
                </p>
              </div>
              {doc.folder && (
                <div>
                  <span className="text-sm text-gray-500">โฟลเดอร์:</span>
                  <p className="font-medium" style={{ color: doc.folder.color }}>
                    {doc.folder.name}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
