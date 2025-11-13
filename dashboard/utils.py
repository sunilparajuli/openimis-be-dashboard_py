from core.models import InteractiveUser
from location.models import HealthFacility
from core.utils import filter_validity

def get_current_user_hf(user):
    """
    The HealthFacility object linked to the currently logged-in user
    via InteractiveUser.health_facility_id.
    Returns None if the user is not authenticated or has no associated health facility.
    """
    if not user or not user.is_authenticated:
        return None

    try:
        i_user = InteractiveUser.objects.filter(
                login_name__iexact=user.username,
                *filter_validity()).first()
        hf_id = i_user.health_facility_id
        if hf_id:
            return hf_id
        return None
    except InteractiveUser.DoesNotExist:
        return None
    except HealthFacility.DoesNotExist:
        return None
    except Exception as e:
        return None
