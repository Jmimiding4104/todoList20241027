from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import asyncio


app = FastAPI()

# 定義一個資料模型


class todoList(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str
    completed: bool = False

    class Config:
        # 設置 ORM 模式以便於處理 MongoDB 的 ObjectId
        json_encoders = {
            ObjectId: str
        }


# 資料庫
dbName = 'python'
collectionName = '2024py'
client = MongoClient(
    "mongodb+srv://jmimiding4104:aaaa1111@cluster0.paad7v9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
database = client[dbName]
collection = database[collectionName]

# 確認資料庫連結成功與否


async def connect_to_mongo():
    try:
        # 測試 ping 值，若沒有回應就會走 except 回報未連結
        await asyncio.to_thread(client.admin.command, 'ping')
        print("MongoDB 連接成功")
    except Exception as e:
        print(f"MongoDB 連接失敗: {e}")

# 開始時執行確認函式


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()


# 取得所有 todoList
@app.get("/todos/", response_model=List[todoList])
async def get_all_todos():
    todos = []
    for todo in collection.find():
        todo['_id'] = str(todo['_id'])
        todos.append(todo)

    return todos


# 建立新的 todoList
@app.post("/todos/", response_model=todoList)
async def create_todo(todo: todoList):
    todo_dict = todo.dict()
    collection.insert_one(todo_dict)
    return todo


# 取得單一資料
@app.get("/todos/{id}", response_model=todoList)
async def get_one_todos(id: str):
    todo_id = ObjectId(id)
    result = collection.find_one({"_id": todo_id})
    print(result)
    if result:
        result['_id'] = str(result['_id'])
        return result
    else:
        raise HTTPException(status_code=404, detail="未找到資料")

# 更新 ToDo


@app.put("/todos/{id}", response_model=todoList)
async def update_todo(id: str, updatedTodo: todoList):
    todo_id = ObjectId(id)
    result = collection.update_one(
        {"_id": todo_id},  # 查找條件
        {"$set": {"title": updatedTodo.title, "description": updatedTodo.description,
                  "completed": updatedTodo.completed}}
    )
    if result.matched_count > 0:
        updated_todo = await get_one_todos(id)
        return updated_todo
    else:
        raise HTTPException(status_code=404, detail="未找到資料")


# 刪除 ToDo
@app.delete("/todos/{id}", response_model=todoList)
async def delete_todo(id: str):
    todo_id = ObjectId(id)
    result = collection.delete_one({"_id": todo_id})

    if result.deleted_count > 0:
        raise HTTPException(status_code=200, detail="刪除成功")
    else:
        raise HTTPException(status_code=404, detail="請確認 ID")
