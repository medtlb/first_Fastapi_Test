
from typing import List, Optional

from sqlalchemy import func
from .. import models, schema,oauth2
from fastapi import FastAPI, HTTPException, Response,status,Depends, APIRouter
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)



#-----------------------------------------------------------
@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schema.Post)
def createPost(post: schema.PostCreate,db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
      
    #new_post = models.Post(title = post.title, content = post.content, published = post.published)
    #new_post = models.Post(**post.model_dump())
    new_post = models.Post(owner_id = current_user.id,**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
#----------------------------------------------------------
@router.get("/",response_model=List[schema.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user),limit:int = 10,skip: int = 0 ,search : Optional[str]=""):
    #posts = db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    # posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
         models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).all()
    return results

 
 

#----------------------------------------------------------
@router.get("/{id}",response_model=schema.PostOut)
def get_post(id: int,db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
   # print(current_user.email)
    #post = db.query(models.Post).filter(models.Post.id==id).first()
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
         models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.id==id).first()

    if not results:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"post with id :{id} was not found")
    # if post.owner_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,=
    #                         detail="Not authorized to preform requested action")
    return  results

#-----------------------------------------------------------
@router.put("/{id}",response_model=schema.PostOut)
def update_post(id:int, post_updated: schema.PostCreate,db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #   updated_post = db.query(models.Post).filter(models.Post.id == id)
    #   post = updated_post.first()
      updated_post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
         models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.id == id)
      post = updated_post.first()

      if post == None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"post with id :{id} does not exist")
      if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to preform requested action")
      
      updated_post.update(post_updated.dict(),synchronize_session=False)
      db.commit()
      return updated_post.first()

 
#----------------------------------------------------------- 
@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int,db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    deleted_post = db.query(models.Post).filter(models.Post.id==id)
    post = deleted_post.first()

    if post == None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"post with id :{id} was not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to preform requested action")
    deleted_post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)