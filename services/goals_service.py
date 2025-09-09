import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class GoalsService:
    """Service for managing portfolio goals and milestones."""
    
    def __init__(self, config_path: str = "data/goals.json"):
        self.config_path = Path(config_path)
        self.current_goal = None
        self._load_goals()
    
    def _load_goals(self) -> None:
        """Load goals from persistent storage."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.current_goal = data.get('current_goal')
                    logger.info("Goals loaded successfully")
            else:
                logger.info("No existing goals file found")
        except Exception as e:
            logger.error(f"Error loading goals: {e}")
            self.current_goal = None
    
    def _save_goals(self) -> bool:
        """Save goals to persistent storage."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "current_goal": self.current_goal,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Goals saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving goals: {e}")
            return False
    
    def create_goal(self, metric: str, milestones: List[Dict]) -> bool:
        """Create a new goal with milestones."""
        try:
            # Validate milestones
            if not self._validate_milestones(milestones):
                return False
            
            # Update milestone statuses
            updated_milestones = self._update_milestone_statuses(milestones, 0)
            
            self.current_goal = {
                "metric": metric,
                "milestones": updated_milestones,
                "active": True,
                "created_date": datetime.now().isoformat()
            }
            
            return self._save_goals()
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return False
    
    def update_goal(self, metric: str, milestones: List[Dict]) -> bool:
        """Update existing goal."""
        return self.create_goal(metric, milestones)
    
    def get_current_goal(self) -> Optional[Dict]:
        """Get current active goal."""
        return self.current_goal
    
    def calculate_progress(self, current_value: float) -> Dict:
        """Calculate goal progress for both view modes."""
        if not self.current_goal:
            return None
        
        milestones = self.current_goal["milestones"]
        updated_milestones = self._update_milestone_statuses(milestones, current_value)
        
        # Update stored goal with new statuses
        self.current_goal["milestones"] = updated_milestones
        self._save_goals()
        
        # Calculate overall progress
        total_target = milestones[-1]["amount"]
        overall_progress = min(current_value / total_target * 100, 100)
        
        # Calculate next milestone progress
        next_milestone_data = self._get_next_milestone_progress(current_value, updated_milestones)
        
        return {
            "current_value": current_value,
            "overall": {
                "progress_percent": overall_progress,
                "target": total_target,
                "text": f"${current_value:,.0f} / ${total_target:,.0f} ({overall_progress:.1f}%)"
            },
            "next_milestone": next_milestone_data,
            "milestones": updated_milestones
        }
    
    def _validate_milestones(self, milestones: List[Dict]) -> bool:
        """Validate milestone configuration."""
        if not milestones:
            return False
        
        # Check ascending amounts
        amounts = [m["amount"] for m in milestones]
        if amounts != sorted(amounts):
            logger.error("Milestone amounts must be in ascending order")
            return False
        
        # Check unique labels
        labels = [m["label"] for m in milestones]
        if len(labels) != len(set(labels)):
            logger.error("Milestone labels must be unique")
            return False
        
        return True
    
    def _update_milestone_statuses(self, milestones: List[Dict], current_value: float) -> List[Dict]:
        """Update milestone statuses based on current value."""
        updated = []
        for milestone in milestones:
            milestone_copy = milestone.copy()
            if current_value >= milestone["amount"]:
                milestone_copy["status"] = "reached"
            else:
                milestone_copy["status"] = "upcoming"
            updated.append(milestone_copy)
        return updated
    
    def _get_next_milestone_progress(self, current_value: float, milestones: List[Dict]) -> Dict:
        """Calculate progress to next unreached milestone."""
        # Find next unreached milestone
        next_milestone = None
        prev_amount = 0
        
        for milestone in milestones:
            if milestone["status"] == "upcoming":
                next_milestone = milestone
                break
            prev_amount = milestone["amount"]
        
        if not next_milestone:
            # All milestones reached
            return {
                "progress_percent": 100,
                "target": milestones[-1]["amount"],
                "text": "All milestones completed! 🎉",
                "label": "Completed"
            }
        
        # Calculate progress within current segment
        segment_start = prev_amount
        segment_end = next_milestone["amount"]
        segment_size = segment_end - segment_start
        
        if segment_size > 0:
            segment_progress = max(0, current_value - segment_start)
            progress_percent = min(segment_progress / segment_size * 100, 100)
        else:
            progress_percent = 0
        
        return {
            "progress_percent": progress_percent,
            "target": next_milestone["amount"],
            "label": next_milestone["label"],
            "text": f"Towards {next_milestone['label']}: ${current_value:,.0f} → ${next_milestone['amount']:,.0f} ({progress_percent:.1f}%)"
        }
    
    def delete_goal(self) -> bool:
        """Delete current goal."""
        try:
            self.current_goal = None
            return self._save_goals()
        except Exception as e:
            logger.error(f"Error deleting goal: {e}")
            return False
    
    def has_active_goal(self) -> bool:
        """Check if there's an active goal."""
        return self.current_goal is not None and self.current_goal.get("active", False)
