"""
Verification module for SourceFinder API.

This module provides functionality to verify information across multiple sources
and implement stimulated verification techniques to assess information reliability.
"""

from typing import Dict, List, Optional, Tuple, Any
import re
from datetime import datetime
import numpy as np
from pydantic import BaseModel

class VerificationResult(BaseModel):
    """Model for verification results."""
    is_verified: bool
    confidence_score: float
    verification_method: str
    supporting_sources: List[str]
    conflicting_sources: List[str]
    verification_details: Dict[str, Any]

class SourceVerifier:
    """
    Class for verifying information across multiple sources.
    
    This class implements various verification techniques to assess
    the reliability of information found across different sources.
    """
    
    def __init__(self):
        """Initialize the SourceVerifier."""
        self.verification_methods = {
            "cross_reference": self._cross_reference_verification,
            "fact_checking": self._fact_checking_verification,
            "source_credibility": self._source_credibility_verification,
            "temporal_analysis": self._temporal_analysis_verification,
            "stimulated_verification": self._stimulated_verification
        }
    
    def verify_information(self, 
                          information: str, 
                          sources: List[Dict[str, Any]], 
                          method: str = "cross_reference") -> VerificationResult:
        """
        Verify information across multiple sources.
        
        Args:
            information: The information to verify
            sources: List of sources containing the information
            method: Verification method to use
            
        Returns:
            VerificationResult object containing verification details
        """
        if method not in self.verification_methods:
            raise ValueError(f"Unknown verification method: {method}")
            
        return self.verification_methods[method](information, sources)
    
    def _cross_reference_verification(self, 
                                     information: str, 
                                     sources: List[Dict[str, Any]]) -> VerificationResult:
        """
        Verify information by cross-referencing across multiple sources.
        
        This method checks if the same information appears in multiple sources
        and assesses the consistency of reporting.
        """
        # Extract key facts from the information
        key_facts = self._extract_key_facts(information)
        
        # Check each source for the key facts
        supporting_sources = []
        conflicting_sources = []
        fact_scores = {}
        
        for source in sources:
            source_text = source.get("snippet", "")
            source_id = source.get("id", "")
            
            # Check each key fact against the source
            for fact in key_facts:
                if fact in source_text:
                    if fact not in fact_scores:
                        fact_scores[fact] = []
                    fact_scores[fact].append(source_id)
                    if source_id not in supporting_sources:
                        supporting_sources.append(source_id)
                else:
                    # Check for conflicting information
                    if self._has_conflicting_information(fact, source_text):
                        if source_id not in conflicting_sources:
                            conflicting_sources.append(source_id)
        
        # Calculate verification score
        verification_score = self._calculate_verification_score(fact_scores, len(key_facts))
        
        # Determine if information is verified
        is_verified = verification_score >= 0.7 and len(supporting_sources) >= 2
        
        return VerificationResult(
            is_verified=is_verified,
            confidence_score=verification_score,
            verification_method="cross_reference",
            supporting_sources=supporting_sources,
            conflicting_sources=conflicting_sources,
            verification_details={
                "key_facts": key_facts,
                "fact_scores": fact_scores
            }
        )
    
    def _fact_checking_verification(self, 
                                   information: str, 
                                   sources: List[Dict[str, Any]]) -> VerificationResult:
        """
        Verify information using fact-checking techniques.
        
        This method implements basic fact-checking by looking for
        specific patterns and inconsistencies in the information.
        """
        # Check for common misinformation patterns
        misinformation_patterns = [
            r"conspiracy",
            r"hoax",
            r"fake news",
            r"misinformation",
            r"disinformation",
            r"unverified",
            r"unconfirmed",
            r"rumor",
            r"speculation"
        ]
        
        # Check for reliable information patterns
        reliable_patterns = [
            r"according to",
            r"reported by",
            r"confirmed by",
            r"verified",
            r"official",
            r"statement",
            r"announcement",
            r"press release"
        ]
        
        # Count occurrences of each pattern
        misinformation_count = sum(
            len(re.findall(pattern, information.lower())) 
            for pattern in misinformation_patterns
        )
        
        reliable_count = sum(
            len(re.findall(pattern, information.lower())) 
            for pattern in reliable_patterns
        )
        
        # Calculate verification score
        total_patterns = misinformation_count + reliable_count
        if total_patterns == 0:
            verification_score = 0.5  # Neutral score if no patterns found
        else:
            verification_score = reliable_count / total_patterns
        
        # Determine if information is verified
        is_verified = verification_score >= 0.7
        
        return VerificationResult(
            is_verified=is_verified,
            confidence_score=verification_score,
            verification_method="fact_checking",
            supporting_sources=[],
            conflicting_sources=[],
            verification_details={
                "misinformation_count": misinformation_count,
                "reliable_count": reliable_count
            }
        )
    
    def _source_credibility_verification(self, 
                                        information: str, 
                                        sources: List[Dict[str, Any]]) -> VerificationResult:
        """
        Verify information based on source credibility.
        
        This method assesses the credibility of sources based on
        various factors such as domain reputation, author credentials, etc.
        """
        # Define credible domains (in a real implementation, this would be more extensive)
        credible_domains = [
            "reuters.com",
            "apnews.com",
            "bbc.com",
            "nytimes.com",
            "washingtonpost.com",
            "theguardian.com",
            "cnn.com",
            "npr.org",
            "scientificamerican.com",
            "nature.com",
            "science.org",
            "who.int",
            "cdc.gov",
            "nih.gov",
            "gov",
            "edu"
        ]
        
        # Define less credible domains
        less_credible_domains = [
            "blogspot.com",
            "wordpress.com",
            "medium.com",
            "tumblr.com",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "tiktok.com"
        ]
        
        # Assess source credibility
        credible_sources = []
        less_credible_sources = []
        
        for source in sources:
            source_url = source.get("link", "")
            source_id = source.get("id", "")
            
            is_credible = any(domain in source_url for domain in credible_domains)
            is_less_credible = any(domain in source_url for domain in less_credible_domains)
            
            if is_credible:
                credible_sources.append(source_id)
            elif is_less_credible:
                less_credible_sources.append(source_id)
        
        # Calculate verification score
        total_sources = len(sources)
        if total_sources == 0:
            verification_score = 0.5  # Neutral score if no sources
        else:
            verification_score = len(credible_sources) / total_sources
        
        # Determine if information is verified
        is_verified = verification_score >= 0.7 and len(credible_sources) >= 2
        
        return VerificationResult(
            is_verified=is_verified,
            confidence_score=verification_score,
            verification_method="source_credibility",
            supporting_sources=credible_sources,
            conflicting_sources=less_credible_sources,
            verification_details={
                "credible_sources_count": len(credible_sources),
                "less_credible_sources_count": len(less_credible_sources)
            }
        )
    
    def _temporal_analysis_verification(self, 
                                       information: str, 
                                       sources: List[Dict[str, Any]]) -> VerificationResult:
        """
        Verify information using temporal analysis.
        
        This method analyzes the timing of sources to determine
        if information has evolved or been corrected over time.
        """
        # Extract dates from sources
        dated_sources = []
        for source in sources:
            if "date" in source:
                try:
                    date = datetime.fromisoformat(source["date"].replace("Z", "+00:00"))
                    dated_sources.append((source["id"], date))
                except (ValueError, TypeError):
                    pass
        
        # Sort sources by date
        dated_sources.sort(key=lambda x: x[1])
        
        # Check for information evolution
        information_evolution = []
        if len(dated_sources) >= 2:
            for i in range(1, len(dated_sources)):
                source_id = dated_sources[i][0]
                source = next((s for s in sources if s["id"] == source_id), None)
                if source:
                    information_evolution.append(source_id)
        
        # Calculate verification score
        if len(dated_sources) == 0:
            verification_score = 0.5  # Neutral score if no dated sources
        else:
            # Higher score if information is consistent across time
            verification_score = 1.0 - (len(information_evolution) / len(dated_sources))
        
        # Determine if information is verified
        is_verified = verification_score >= 0.7 and len(dated_sources) >= 2
        
        return VerificationResult(
            is_verified=is_verified,
            confidence_score=verification_score,
            verification_method="temporal_analysis",
            supporting_sources=[s[0] for s in dated_sources],
            conflicting_sources=information_evolution,
            verification_details={
                "dated_sources_count": len(dated_sources),
                "information_evolution": information_evolution
            }
        )
    
    def _stimulated_verification(self, 
                                information: str, 
                                sources: List[Dict[str, Any]]) -> VerificationResult:
        """
        Verify information using stimulated verification techniques.
        
        This method implements a more advanced verification approach
        that stimulates different verification scenarios to assess
        information reliability.
        """
        # Combine multiple verification methods
        cross_ref_result = self._cross_reference_verification(information, sources)
        fact_check_result = self._fact_checking_verification(information, sources)
        source_cred_result = self._source_credibility_verification(information, sources)
        temporal_result = self._temporal_analysis_verification(information, sources)
        
        # Calculate weighted verification score
        weights = {
            "cross_reference": 0.3,
            "fact_checking": 0.2,
            "source_credibility": 0.3,
            "temporal_analysis": 0.2
        }
        
        verification_score = (
            cross_ref_result.confidence_score * weights["cross_reference"] +
            fact_check_result.confidence_score * weights["fact_checking"] +
            source_cred_result.confidence_score * weights["source_credibility"] +
            temporal_result.confidence_score * weights["temporal_analysis"]
        )
        
        # Combine supporting and conflicting sources
        supporting_sources = list(set(
            cross_ref_result.supporting_sources +
            source_cred_result.supporting_sources +
            temporal_result.supporting_sources
        ))
        
        conflicting_sources = list(set(
            cross_ref_result.conflicting_sources +
            source_cred_result.conflicting_sources +
            temporal_result.conflicting_sources
        ))
        
        # Determine if information is verified
        is_verified = verification_score >= 0.7 and len(supporting_sources) >= 2
        
        return VerificationResult(
            is_verified=is_verified,
            confidence_score=verification_score,
            verification_method="stimulated_verification",
            supporting_sources=supporting_sources,
            conflicting_sources=conflicting_sources,
            verification_details={
                "cross_reference_score": cross_ref_result.confidence_score,
                "fact_checking_score": fact_check_result.confidence_score,
                "source_credibility_score": source_cred_result.confidence_score,
                "temporal_analysis_score": temporal_result.confidence_score
            }
        )
    
    def _extract_key_facts(self, information: str) -> List[str]:
        """Extract key facts from information text."""
        # Simple implementation - split by sentences and filter
        sentences = re.split(r'[.!?]+', information)
        key_facts = [s.strip() for s in sentences if len(s.strip()) > 10]
        return key_facts
    
    def _has_conflicting_information(self, fact: str, text: str) -> bool:
        """Check if text contains information conflicting with the fact."""
        # Simple implementation - look for negation patterns
        negation_patterns = [
            r"not",
            r"never",
            r"didn't",
            r"doesn't",
            r"haven't",
            r"hasn't",
            r"won't",
            r"wouldn't",
            r"couldn't",
            r"shouldn't",
            r"isn't",
            r"aren't",
            r"wasn't",
            r"weren't"
        ]
        
        # Check if text contains the fact and a negation
        has_fact = fact.lower() in text.lower()
        has_negation = any(pattern in text.lower() for pattern in negation_patterns)
        
        return has_fact and has_negation
    
    def _calculate_verification_score(self, fact_scores: Dict[str, List[str]], total_facts: int) -> float:
        """Calculate verification score based on fact scores."""
        if total_facts == 0:
            return 0.5  # Neutral score if no facts
            
        # Calculate score for each fact
        fact_verification_scores = []
        for fact, sources in fact_scores.items():
            # More sources = higher score
            source_count = len(sources)
            if source_count >= 3:
                fact_score = 1.0
            elif source_count == 2:
                fact_score = 0.8
            elif source_count == 1:
                fact_score = 0.5
            else:
                fact_score = 0.0
                
            fact_verification_scores.append(fact_score)
        
        # Calculate overall score
        return sum(fact_verification_scores) / total_facts 