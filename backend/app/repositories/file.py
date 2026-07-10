from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import File, FileVersion, DeletedFile, FileAnnotation, ShareLink

class FileRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, fid: str) -> File | None: return await self._s.get(File, fid)
    async def list_by_folder(self, folder_id: str) -> list[File]:
        r = await self._s.execute(select(File).where(File.folder_id == folder_id))
        return list(r.scalars().all())
    async def create(self, f: File) -> File: self._s.add(f); await self._s.flush(); return f
    async def update(self, f: File) -> File: await self._s.flush(); return f
    async def delete(self, f: File) -> None: await self._s.delete(f); await self._s.flush()
    async def list_all(self) -> list[File]:
        r = await self._s.execute(select(File))
        return list(r.scalars().all())

class FileVersionRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_file(self, file_id: str) -> list[FileVersion]:
        r = await self._s.execute(select(FileVersion).where(FileVersion.file_id == file_id).order_by(FileVersion.version_no.desc()))
        return list(r.scalars().all())
    async def create(self, v: FileVersion) -> FileVersion: self._s.add(v); await self._s.flush(); return v

class AnnotationRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_file(self, file_id: str) -> list[FileAnnotation]:
        r = await self._s.execute(select(FileAnnotation).where(FileAnnotation.file_id == file_id, FileAnnotation.parent_id == None))
        return list(r.scalars().all())
    async def create(self, a: FileAnnotation) -> FileAnnotation: self._s.add(a); await self._s.flush(); return a
    async def delete(self, a: FileAnnotation) -> None: await self._s.delete(a); await self._s.flush()
    async def get_by_id(self, aid: str) -> FileAnnotation | None: return await self._s.get(FileAnnotation, aid)

class DeletedFileRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_all(self) -> list[DeletedFile]:
        r = await self._s.execute(select(DeletedFile))
        return list(r.scalars().all())
    async def create(self, d: DeletedFile) -> DeletedFile: self._s.add(d); await self._s.flush(); return d
    async def delete(self, d: DeletedFile) -> None: await self._s.delete(d); await self._s.flush()

class ShareLinkRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_token(self, token: str) -> ShareLink | None:
        r = await self._s.execute(select(ShareLink).where(ShareLink.token == token))
        return r.scalar_one_or_none()
    async def create(self, sl: ShareLink) -> ShareLink: self._s.add(sl); await self._s.flush(); return sl
