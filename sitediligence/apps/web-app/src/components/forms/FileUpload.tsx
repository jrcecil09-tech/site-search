import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File } from 'lucide-react'
import { cn } from '@/lib/utils'

const ACCEPTED = {
  'application/json': ['.geojson', '.json'],
  'application/octet-stream': ['.dxf', '.shp', '.dbf', '.prj', '.shx', '.gpx'],
  'application/vnd.google-earth.kml+xml': ['.kml'],
}

interface FileUploadProps {
  onFiles: (files: File[]) => void
  label?: string
  multiple?: boolean
}

export function FileUpload({ onFiles, label = 'Drop GIS files here', multiple = true }: FileUploadProps) {
  const onDrop = useCallback((accepted: File[]) => onFiles(accepted), [onFiles])

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple,
  })

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          isDragActive ? 'border-navy bg-navy/5' : 'border-gray-300 hover:border-navy/50',
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
        <p className="text-sm text-gray-600">{label}</p>
        <p className="text-xs text-gray-400 mt-1">GeoJSON · DXF · Shapefile · KML · GPX</p>
      </div>
      {acceptedFiles.length > 0 && (
        <ul className="space-y-1">
          {acceptedFiles.map((f) => (
            <li key={f.name} className="flex items-center gap-2 text-xs text-gray-600">
              <File className="w-3 h-3 text-navy" />
              {f.name} <span className="text-gray-400">({(f.size / 1024).toFixed(1)} KB)</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
