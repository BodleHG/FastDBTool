-- GLB 파일 저장을 위한 테이블 스키마
CREATE TABLE IF NOT EXISTS glb_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) DEFAULT 'model/gltf-binary',
    file_data LONGBLOB NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    tags JSON,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    -- 인덱스 추가
    INDEX idx_filename (filename),
    INDEX idx_upload_time (upload_time),
    INDEX idx_file_hash (file_hash),
    INDEX idx_is_active (is_active),
    
    -- 유니크 제약조건
    UNIQUE KEY unique_filename (filename),
    UNIQUE KEY unique_file_hash (file_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 파일 메타데이터만 저장하는 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS glb_file_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    metadata_key VARCHAR(100) NOT NULL,
    metadata_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES glb_files(id) ON DELETE CASCADE,
    INDEX idx_file_id (file_id),
    INDEX idx_metadata_key (metadata_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 파일 접근 로그 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS glb_file_access_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    access_type ENUM('download', 'view', 'upload', 'delete') NOT NULL,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_ip VARCHAR(45),
    user_agent TEXT,
    
    FOREIGN KEY (file_id) REFERENCES glb_files(id) ON DELETE CASCADE,
    INDEX idx_file_id (file_id),
    INDEX idx_access_time (access_time),
    INDEX idx_access_type (access_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 