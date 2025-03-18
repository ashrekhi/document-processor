from fastapi import APIRouter, Form, HTTPException, Depends
from app.services.s3_service import S3Service

router = APIRouter()

# Dependency to get S3 service
def get_s3_service():
    return S3Service()

@router.get("/")
async def get_folders(s3_service: S3Service = Depends(get_s3_service)):
    """
    Get information about available folders in the master bucket.
    """
    try:
        folders = s3_service.list_folders()
        return {
            "folders": folders,
            "master_bucket": s3_service.master_bucket
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting folders: {str(e)}")

@router.post("/")
async def create_folder(
    folder_name: str = Form(...),
    s3_service: S3Service = Depends(get_s3_service)
):
    """
    Create a new folder in the master bucket.
    """
    try:
        s3_url = s3_service.create_folder(folder_name)
        return {"message": f"Folder {folder_name} created successfully", "s3_url": s3_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

@router.delete("/{folder_name}")
async def delete_folder(
    folder_name: str,
    s3_service: S3Service = Depends(get_s3_service)
):
    """
    Delete a folder and all its contents.
    Also deletes the corresponding Pinecone namespace.
    """
    try:
        print(f"FOLDER DELETE ENDPOINT: Starting deletion of folder '{folder_name}'")
        print(f"FOLDER DELETE ENDPOINT: This will also delete the corresponding Pinecone namespace")
        
        success = s3_service.delete_folder(folder_name)
        if success:
            print(f"FOLDER DELETE ENDPOINT: Successfully deleted folder '{folder_name}' and its Pinecone namespace")
            return {"message": f"Folder {folder_name} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete folder {folder_name}")
    except Exception as e:
        print(f"FOLDER DELETE ENDPOINT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting folder: {str(e)}") 