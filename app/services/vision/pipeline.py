"""Hybrid image processing pipeline: OCR + conditional vision analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.vision.ocr import extract_text_from_bytes
from app.services.vision.analyzer import (
    analyze_with_vision,
    classify_image_complexity,
)


@dataclass
class ImageAnalysisResult:
    """Result of hybrid image analysis."""
    
    ocr_text: str
    """Text extracted via OCR"""
    
    complexity: Literal["simple_text", "complex_reasoning"]
    """Classification of image complexity"""
    
    vision_analysis: str | None = None
    """Vision model analysis (only for complex images)"""
    
    combined_output: str = ""
    """Final combined analysis output"""
    
    def format_output(self) -> str:
        """Format the analysis result for display/response."""
        sections = []
        
        if self.complexity == "simple_text":
            sections.append("**TEXT EXTRACTION RESULT:**")
            sections.append(self.ocr_text)
        else:
            # Complex reasoning
            sections.append("**IMAGE ANALYSIS RESULT:**")
            if self.vision_analysis:
                sections.append(self.vision_analysis)
            
            if self.ocr_text.strip():
                sections.append("\n**EXTRACTED TEXT:**")
                sections.append(self.ocr_text)
        
        return "\n".join(sections)


def process_image_hybrid(
    image_bytes: bytes,
    image_url: str | None = None,
    custom_query: str | None = None,
) -> ImageAnalysisResult:
    """
    Hybrid image processing pipeline.
    
    Process flow:
    1. Extract text via OCR
    2. Classify image complexity (simple text vs complex reasoning)
    3. For simple text: return OCR only
    4. For complex: add vision model analysis + OCR text
    
    Args:
        image_bytes: Raw image bytes
        image_url: Original URL (for logging/reference)
        custom_query: Custom vision query (overrides default)
    
    Returns:
        ImageAnalysisResult with OCR, classification, and optional vision analysis
    """
    print(f"[Pipeline] Processing image: {image_url or 'bytes'}")
    
    # Step 1: OCR Extraction
    print("[Pipeline] Step 1: OCR extraction...")
    ocr_text = extract_text_from_bytes(image_bytes)
    
    # Step 2: Complexity Classification
    print("[Pipeline] Step 2: Classifying image complexity...")
    image_size_kb = len(image_bytes) / 1024
    complexity = classify_image_complexity(ocr_text, image_size_kb)
    
    # Step 3: Conditional Vision Analysis
    vision_analysis = None
    if complexity == "complex_reasoning":
        print("[Pipeline] Step 3: Running vision analysis for complex image...")
        vision_analysis = analyze_with_vision(image_bytes, custom_query)
    else:
        print("[Pipeline] Step 3: Skipping vision analysis (simple text detected)")
    
    # Step 4: Combine Results
    result = ImageAnalysisResult(
        ocr_text=ocr_text,
        complexity=complexity,
        vision_analysis=vision_analysis,
    )
    result.combined_output = result.format_output()
    
    print(f"[Pipeline] Complete. Complexity: {complexity}")
    return result


def process_image_force_vision(
    image_bytes: bytes,
    image_url: str | None = None,
    custom_query: str | None = None,
) -> ImageAnalysisResult:
    """
    Force vision analysis even for simple text images.
    Useful when user explicitly wants detailed image reasoning.
    
    Args:
        image_bytes: Raw image bytes
        image_url: Original URL (for logging/reference)
        custom_query: Custom vision query
    
    Returns:
        ImageAnalysisResult with both OCR and vision analysis
    """
    print(f"[Pipeline] Processing image (force vision): {image_url or 'bytes'}")
    
    # OCR
    print("[Pipeline] Step 1: OCR extraction...")
    ocr_text = extract_text_from_bytes(image_bytes)
    
    # Force vision analysis
    print("[Pipeline] Step 2: Running vision analysis (forced)...")
    vision_analysis = analyze_with_vision(image_bytes, custom_query)
    
    result = ImageAnalysisResult(
        ocr_text=ocr_text,
        complexity="complex_reasoning",  # Treat as complex
        vision_analysis=vision_analysis,
    )
    result.combined_output = result.format_output()
    
    print("[Pipeline] Complete (forced vision analysis)")
    return result
