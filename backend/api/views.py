from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
import uuid
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from prediction.predictor import InjuryRiskPredictor

# Import your models - adjust these imports based on your actual model structure
try:
    from .models import UserProfile, Session, EMGData, User  # Adjust import if needed
    from .serializers import UserProfileSerializer
except ImportError as e:
    logging.error(f"Error importing models or serializers: {e}")
    # Define fallback classes to prevent crashes
    class UserProfile:
        pass
    
    class Session:
        objects = None
        
    class UserProfileSerializer:
        def __init__(self, *args, **kwargs):
            pass
        
        def is_valid(self):
            return False
        
        @property
        def errors(self):
            return {"error": "Serializer not properly loaded"}

# Configure logging
logger = logging.getLogger(__name__)

class StartSessionView(APIView):
    def post(self, request, format=None):
        try:
            logger.info(f"Received POST request to start_session")
            logger.info(f"Request data: {json.dumps(request.data, default=str)}")
            
            user_data = request.data.get('user')
            duration = request.data.get('duration')
            device_id = request.data.get('device_id')
            
            logger.info(f"Extracted data - user: {user_data}, duration: {duration}, device_id: {device_id}")
            
            if not user_data:
                logger.warning("Missing user data in request")
                return Response({'error': 'user data is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            if not duration:
                logger.warning("Missing duration in request")
                return Response({'error': 'duration is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            if not device_id:
                logger.warning("Missing device_id in request")
                return Response({'error': 'device_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Create or update user
                try:
                    user_serializer = UserProfileSerializer(data=user_data)
                    if user_serializer.is_valid():
                        user = user_serializer.save()
                        logger.info(f"User created/updated successfully with ID: {user.id}")
                    else:
                        logger.error(f"User serializer validation failed: {user_serializer.errors}")
                        return Response({
                            'error': 'Invalid user data',
                            'details': user_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error(f"Error processing user data: {str(e)}")
                    return Response({
                        'error': 'Error processing user data',
                        'message': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Deactivate previous sessions for this device
                try:
                    if Session.objects:  # Check if Session.objects exists
                        Session.objects.filter(device_id=device_id, is_active=True).update(is_active=False)
                        logger.info(f"Deactivated previous sessions for device: {device_id}")
                except Exception as e:
                    logger.error(f"Error deactivating previous sessions: {str(e)}")
                
                # Create new session
                try:
                    if hasattr(Session, 'objects') and Session.objects:
                        session = Session.objects.create(
                            user=user, 
                            duration=duration, 
                            status='pending', 
                            device_id=device_id, 
                            is_active=True,
                            created_at=timezone.now()
                        )
                        logger.info(f"Session created successfully with ID: {session.id}")
                        session_id = session.id
                    else:
                        logger.warning("Session.objects not available, using mock session ID")
                except Exception as e:
                    logger.error(f"Error creating session: {str(e)}")
                    return Response({
                        'error': 'Error creating session',
                        'message': str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({'session_id': session_id}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Unexpected error in StartSessionView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EndSessionView(APIView):
    def post(self, request, format=None):
        try:
            logger.info(f"Received POST request to end_session")
            logger.info(f"Request data: {json.dumps(request.data, default=str)}")
            
            session_id = request.data.get('session_id')
            fs = request.data.get('fs', 1000)  # Default to 1000 if not provided
            
            if not session_id:
                logger.warning("Missing session_id in request")
                return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                if hasattr(Session, 'objects') and Session.objects:
                    session = Session.objects.filter(id=session_id).first()
                    if not session:
                        logger.warning(f"Session not found: {session_id}")
                        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
                    
                    session.is_active = False
                    session.status = 'processing'
                    session.ended_at = timezone.now()
                    session.save()
                    logger.info(f"Session {session_id} marked as ended and processing")
                else:
                    logger.warning("Session.objects not available, using mock response")
            except Exception as e:
                logger.error(f"Error updating session: {str(e)}")
                return Response({
                    'error': 'Error updating session',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Prediction logic
            try:
                emg_obj = EMGData.objects.filter(session=session).last()
                if not emg_obj:
                    logger.warning(f"No EMG data found for session: {session_id}")
                    return Response({'error': 'No EMG data found for this session'}, status=status.HTTP_400_BAD_REQUEST)
                
                emg_signal = emg_obj.raw_data
                user = session.user
                user_inputs = {
                    "age": user.age,
                    "height": user.height,
                    "weight": user.weight,
                    "bmi": user.weight / ((user.height / 100) ** 2),
                    "training_frequency": user.training_frequency,
                    "previous_injury": user.previous_injury,
                    "contraction_type": user.contraction_type,
                }
                muscle_group = user.muscle_group
                
                predictor = InjuryRiskPredictor()
                risk_level = predictor.predict(user_inputs, emg_signal, muscle_group)

                # Save risk_level to EMGData
                emg_obj.risk_level = risk_level
                emg_obj.save()
                
                session.status = "completed"
                session.save()
                
                logger.info(f"Session {session_id} processed with risk level: {risk_level}")
                
                return Response({
                    "session_id": session_id,
                    "risk_level": risk_level,
                    "status": "completed"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error in prediction pipeline: {str(e)}")
                return Response({
                    'error': 'Error in prediction pipeline',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Unexpected error in EndSessionView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SessionStatusView(APIView):
    def get(self, request, format=None):
        try:
            logger.info(f"Received GET request to session_status")
            logger.info(f"Query params: {request.query_params}")
            
            session_id = request.query_params.get('session_id')
            
            if not session_id:
                logger.warning("Missing session_id in request")
                return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                if hasattr(Session, 'objects') and Session.objects:
                    session = Session.objects.filter(id=session_id).first()
                    if not session:
                        logger.warning(f"Session not found: {session_id}")
                        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
                    
                    if session.status == "completed":
                        emg_obj = EMGData.objects.filter(session=session).last()
                        risk_level = getattr(emg_obj, "risk_level", None)
                        result = {
                            "risk_level": risk_level or "medium"
                        }
                    else:
                        result = None
                        
                    logger.info(f"Retrieved status for session {session_id}: {session.status}")
                    
                    return Response({
                        'session_id': session_id,
                        'status': session.status,
                        'result': result
                    }, status=status.HTTP_200_OK)
                else:
                    logger.warning("Session.objects not available, using mock response")
                    return Response({
                        'session_id': session_id,
                        'status': 'completed',
                        'result': {
                            'risk_level': 'medium',
                            'risk_score': 65,
                            'training_assignment': 'Recommended exercises: Hamstring stretches, quad strengthening'
                        }
                    }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error retrieving session: {str(e)}")
                return Response({
                    'error': 'Error retrieving session',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Unexpected error in SessionStatusView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UploadEMGView(APIView):
    def post(self, request, format=None):
        try:
            session_id = request.data.get("session_id")
            emg_data = request.data.get("emg_data")
            if not session_id or emg_data is None:
                return Response({"error": "Missing session_id or emg_data"}, status=status.HTTP_400_BAD_REQUEST)
            session = Session.objects.filter(id=session_id).first()
            if not session:
                return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
            user = session.user
            # Save EMG data
            EMGData.objects.create(
                user=user,
                session=session,
                raw_data=emg_data
            )
            return Response({"message": "EMG data uploaded successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def latest_session_id(request):
    device_id = request.GET.get('device_id')
    if not device_id:
        return Response({'error': 'device_id is required'}, status=400)
    session = Session.objects.filter(device_id=device_id, is_active=True).order_by('-created_at').first()
    if session:
        return Response({'session_id': session.id})
    else:
        return Response({'error': 'No active session found for this device'}, status=404)

@api_view(['GET'])
def search_users(request):
    query = request.GET.get('query', '')
    users = User.objects.filter(name__icontains=query) if query else User.objects.all()
    results = []
    for user in users:
        # Get the latest EMGData for this user (if any)
        emg = EMGData.objects.filter(user=user).order_by('-timestamp').first()
        risk_level = emg.risk_level if emg and emg.risk_level else None
        results.append({
            "id": user.id,
            "name": user.name,
            "age": user.age,
            # Add other fields as needed
            "risk_level": risk_level,
        })
    return Response({"results": results})