using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Collections;
using System.Text;
using Newtonsoft.Json;

[System.Serializable]
public class GLBUploadRequest
{
    public string name;
    public string description;
    public string data; // Base64 인코딩된 GLB 데이터
}

[System.Serializable]
public class GLBDownloadResponse
{
    public string name;
    public string description;
    public string data; // Base64 인코딩된 GLB 데이터
    public int file_size;
    public bool success;
}

public class GLBFileManager : MonoBehaviour
{
    [Header("서버 설정")]
    public string serverUrl = "http://localhost:8000";
    
    [Header("테스트 파일")]
    public string testGlbPath = "Assets/Models/test.glb";
    
    // GLB 파일 업로드
    public void UploadGLBFile(string filePath, string description = "")
    {
        StartCoroutine(UploadGLBFileCoroutine(filePath, description));
    }
    
    private IEnumerator UploadGLBFileCoroutine(string filePath, string description)
    {
        try
        {
            // GLB 파일 읽기
            byte[] glbBytes = System.IO.File.ReadAllBytes(filePath);
            string base64Data = Convert.ToBase64String(glbBytes);
            
            // 파일명 추출
            string fileName = System.IO.Path.GetFileName(filePath);
            
            // JSON 데이터 생성
            var uploadData = new GLBUploadRequest
            {
                name = fileName,
                description = description,
                data = base64Data
            };
            
            string jsonData = JsonConvert.SerializeObject(uploadData);
            byte[] jsonBytes = Encoding.UTF8.GetBytes(jsonData);
            
            // HTTP 요청 생성
            using (UnityWebRequest request = new UnityWebRequest($"{serverUrl}/upload-glb/", "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(jsonBytes);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    Debug.Log("GLB 파일 업로드 성공!");
                    Debug.Log(request.downloadHandler.text);
                }
                else
                {
                    Debug.LogError($"GLB 파일 업로드 실패: {request.error}");
                    Debug.LogError(request.downloadHandler.text);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"GLB 파일 업로드 중 오류: {e.Message}");
        }
    }
    
    // GLB 파일 다운로드
    public void DownloadGLBFile(int fileId, string savePath)
    {
        StartCoroutine(DownloadGLBFileCoroutine(fileId, savePath));
    }
    
    private IEnumerator DownloadGLBFileCoroutine(int fileId, string savePath)
    {
        try
        {
            using (UnityWebRequest request = UnityWebRequest.Get($"{serverUrl}/download-glb/{fileId}"))
            {
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    // JSON 응답 파싱
                    var response = JsonConvert.DeserializeObject<GLBDownloadResponse>(request.downloadHandler.text);
                    
                    if (response.success)
                    {
                        // Base64 디코딩
                        byte[] glbBytes = Convert.FromBase64String(response.data);
                        
                        // 파일 저장
                        System.IO.File.WriteAllBytes(savePath, glbBytes);
                        
                        Debug.Log($"GLB 파일 다운로드 성공: {savePath}");
                        Debug.Log($"파일명: {response.name}");
                        Debug.Log($"설명: {response.description}");
                        Debug.Log($"파일 크기: {response.file_size} bytes");
                    }
                    else
                    {
                        Debug.LogError("GLB 파일 다운로드 실패");
                    }
                }
                else
                {
                    Debug.LogError($"GLB 파일 다운로드 실패: {request.error}");
                    Debug.LogError(request.downloadHandler.text);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"GLB 파일 다운로드 중 오류: {e.Message}");
        }
    }
    
    // GLB 파일 목록 조회
    public void ListGLBFiles()
    {
        StartCoroutine(ListGLBFilesCoroutine());
    }
    
    private IEnumerator ListGLBFilesCoroutine()
    {
        try
        {
            using (UnityWebRequest request = UnityWebRequest.Get($"{serverUrl}/list-glb/"))
            {
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    Debug.Log("GLB 파일 목록:");
                    Debug.Log(request.downloadHandler.text);
                }
                else
                {
                    Debug.LogError($"파일 목록 조회 실패: {request.error}");
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"파일 목록 조회 중 오류: {e.Message}");
        }
    }
    
    // 서버 상태 확인
    public void CheckServerHealth()
    {
        StartCoroutine(CheckServerHealthCoroutine());
    }
    
    private IEnumerator CheckServerHealthCoroutine()
    {
        try
        {
            using (UnityWebRequest request = UnityWebRequest.Get($"{serverUrl}/health"))
            {
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    Debug.Log("서버 상태: 정상");
                    Debug.Log(request.downloadHandler.text);
                }
                else
                {
                    Debug.LogError($"서버 상태 확인 실패: {request.error}");
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"서버 상태 확인 중 오류: {e.Message}");
        }
    }
    
    // UI 버튼용 메서드들
    [ContextMenu("테스트 GLB 파일 업로드")]
    public void TestUploadGLB()
    {
        if (System.IO.File.Exists(testGlbPath))
        {
            UploadGLBFile(testGlbPath, "Unity에서 업로드한 테스트 파일");
        }
        else
        {
            Debug.LogWarning($"테스트 파일을 찾을 수 없습니다: {testGlbPath}");
        }
    }
    
    [ContextMenu("파일 목록 조회")]
    public void TestListFiles()
    {
        ListGLBFiles();
    }
    
    [ContextMenu("서버 상태 확인")]
    public void TestServerHealth()
    {
        CheckServerHealth();
    }
    
    [ContextMenu("테스트 GLB 파일 다운로드")]
    public void TestDownloadGLB()
    {
        string savePath = "Assets/Models/downloaded_test.glb";
        DownloadGLBFile(1, savePath); // ID 1번 파일 다운로드
    }
}

// Unity UI 버튼용 간단한 스크립트
public class GLBFileUI : MonoBehaviour
{
    public GLBFileManager glbManager;
    
    public void OnUploadButtonClick()
    {
        if (glbManager != null)
        {
            glbManager.TestUploadGLB();
        }
    }
    
    public void OnDownloadButtonClick()
    {
        if (glbManager != null)
        {
            glbManager.TestDownloadGLB();
        }
    }
    
    public void OnListButtonClick()
    {
        if (glbManager != null)
        {
            glbManager.TestListFiles();
        }
    }
    
    public void OnHealthButtonClick()
    {
        if (glbManager != null)
        {
            glbManager.CheckServerHealth();
        }
    }
} 