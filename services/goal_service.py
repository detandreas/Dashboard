import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class GoalService:
    """Service για διαχείριση στόχων και milestones του χαρτοφυλακίου."""
    
    def __init__(self, config):
        self.config = config
        self.goals_file = "data/goals.json"
        self._ensure_data_directory()
    
    def _ensure_data_directory(self) -> None:
        """Διασφαλίζει ότι υπάρχει ο φάκελος data."""
        os.makedirs("data", exist_ok=True)
    
    def get_current_goal(self) -> Optional[Dict[str, Any]]:
        """Επιστρέφει τον τρέχοντα ενεργό στόχο."""
        try:
            if os.path.exists(self.goals_file):
                with open(self.goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('current_goal')
            return None
        except Exception as e:
            logger.error(f"Error loading current goal: {e}")
            return None
    
    def save_goal(self, milestones: List[Dict[str, Any]]) -> bool:
        """Αποθηκεύει νέο στόχο με milestones."""
        try:
            # Ταξινόμηση milestones κατά αύξουσα σειρά αξίας
            sorted_milestones = sorted(milestones, key=lambda x: x['amount'])
            
            goal_data = {
                "metric": "portfolio_value",
                "milestones": sorted_milestones,
                "active": True,
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Μόνο current_goal, χωρίς goal_history
            data = {
                "current_goal": goal_data
            }
            
            with open(self.goals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Goal saved successfully with {len(milestones)} milestones")
            return True
            
        except Exception as e:
            logger.error(f"Error saving goal: {e}")
            return False
    
    
    def update_milestone_status(self, current_portfolio_value: float) -> Dict[str, Any]:
        """Ενημερώνει την κατάσταση των milestones βάσει της τρέχουσας αξίας."""
        goal = self.get_current_goal()
        if not goal:
            return {"has_goal": False}
        
        milestones = goal.get("milestones", [])
        updated_milestones = []
        next_milestone = None
        completed_count = 0
        
        for milestone in milestones:
            milestone_copy = milestone.copy()
            if current_portfolio_value >= milestone["amount"]:
                milestone_copy["status"] = "completed"
                completed_count += 1
            else:
                milestone_copy["status"] = "upcoming"
                if next_milestone is None:
                    next_milestone = milestone_copy
            
            updated_milestones.append(milestone_copy)
        
        # Υπολογισμός προόδου
        total_milestones = len(milestones)
        progress_percentage = (completed_count / total_milestones * 100) if total_milestones > 0 else 0
        
        # Εύρεση του τελικού στόχου
        final_goal = max(milestones, key=lambda x: x["amount"]) if milestones else None
        final_goal_progress = 0
        if final_goal:
            final_goal_progress = min((current_portfolio_value / final_goal["amount"]) * 100, 100)
        
        return {
            "has_goal": True,
            "milestones": updated_milestones,
            "next_milestone": next_milestone,
            "completed_count": completed_count,
            "total_count": total_milestones,
            "progress_percentage": progress_percentage,
            "final_goal_progress": final_goal_progress,
            "current_value": current_portfolio_value,
            "final_goal_amount": final_goal["amount"] if final_goal else 0,
            "created_date": goal.get("created_date"),
            "is_completed": completed_count == total_milestones
        }
    
    def delete_current_goal(self) -> bool:
        """Διαγράφει τον τρέχοντα στόχο."""
        try:
            if os.path.exists(self.goals_file):
                with open(self.goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data["current_goal"] = None
                
                with open(self.goals_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logger.info("Current goal deleted successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting goal: {e}")
            return False
    
    def get_goal_suggestions(self, current_value: float) -> List[Dict[str, Any]]:
        """Επιστρέφει προτάσεις για milestones βάσει της τρέχουσας αξίας."""
        suggestions = []
        
        # Βασικά milestones βάσει της τρέχουσας αξίας
        if current_value < 5000:
            base_amounts = [5000, 10000, 15000, 25000, 50000]
        elif current_value < 10000:
            base_amounts = [15000, 25000, 50000, 75000, 100000]
        elif current_value < 25000:
            base_amounts = [30000, 50000, 75000, 100000, 150000]
        else:
            base_amounts = [current_value + 25000, current_value + 50000, 
                          current_value + 100000, current_value + 200000, current_value + 500000]
        
        labels = ["Short Term", "Medium Term", "Long Term", "Major Goal", "Ultimate Target"]
        
        for i, amount in enumerate(base_amounts[:5]):
            suggestions.append({
                "amount": int(amount),
                "label": labels[i] if i < len(labels) else f"Goal {i+1}",
                "status": "upcoming"
            })
        
        return suggestions
