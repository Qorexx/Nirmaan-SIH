"""
Pydantic schemas for MPLADS Duplicate Detection ML Service.

All input fields are optional (except id + title) to handle real-world
partial data gracefully. Missing signals are propagated as None and the
scoring layer renormalises weights accordingly.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class Coordinates(BaseModel):
    lat: float
    lng: float


class ProjectRecord(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    constituency: Optional[str] = None
    mp_name: Optional[str] = None
    sanction_amount: Optional[float] = None
    sanction_date: Optional[str] = None
    execution_start: Optional[str] = None
    execution_end: Optional[str] = None
    implementing_agency: Optional[str] = None
    status: Optional[str] = None

    # Support both flat lat/lng and nested coordinates object
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinates: Optional[Coordinates] = None

    @model_validator(mode="after")
    def normalise_coords(self) -> "ProjectRecord":
        """Promote nested coordinates into flat latitude/longitude fields."""
        if self.coordinates is not None:
            if self.latitude is None:
                self.latitude = self.coordinates.lat
            if self.longitude is None:
                self.longitude = self.coordinates.lng
        return self


class ComparePairRequest(BaseModel):
    projectA: ProjectRecord
    projectB: ProjectRecord


class FindDuplicatesRequest(BaseModel):
    projects: list[ProjectRecord]
    threshold: float = Field(default=40.0, ge=0.0, le=100.0,
                             description="Minimum Potential Duplicate Score (0–100) to flag a pair")


class CheckNewProjectRequest(BaseModel):
    new_project: ProjectRecord
    existing_projects: list[ProjectRecord]
    threshold: float = Field(default=40.0, ge=0.0, le=100.0)
