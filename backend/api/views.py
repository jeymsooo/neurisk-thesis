import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, Session
from .serializers import UserProfileSerializer

# Set up logging
logger = logging.getLogger(__name__)

class StartSessionView(APIView):
    """
    POST: /api/start_session/
    Receives user demographics, session duration, and device_id, creates a session, returns session ID.
    """
    def post(self, request, format=None):
        try:
            logger.info(f"Received POST request to start_session")
            logger.info(f"Request data: {request.data}")
            
            user_data = request.data.get('user')
            duration = request.data.get('duration')
            device_id = request.data.get('device_id')
            
            logger.info(f"Extracted - user_data: {user_data}")
            logger.info(f"Extracted - duration: {duration}")
            logger.info(f"Extracted - device_id: {device_id}")
            
            # Validate required fields
            if not user_data:
                logger.error("Missing user data")
                return Response({'error': 'user data is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not duration:
                logger.error("Missing duration")
                return Response({'error': 'duration is required.'}, status=status.HTTP_400_BAD_REQUEST)
                
            if not device_id:
                logger.error("Missing device_id")
                return Response({'error': 'device_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user profile
            logger.info("Creating user profile with serializer")
            user_serializer = UserProfileSerializer(data=user_data)
            
            if user_serializer.is_valid():
                logger.info("User serializer is valid, saving user")
                user = user_serializer.save()
                logger.info(f"User created successfully with ID: {user.id}")
            else:
                logger.error(f"User serializer validation failed: {user_serializer.errors}")
                return Response({
                    'error': 'Invalid user data',
                    'details': user_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Deactivate any previous sessions for this device
            logger.info(f"Deactivating previous sessions for device: {device_id}")
            previous_sessions = Session.objects.filter(device_id=device_id, is_active=True)
            logger.info(f"Found {previous_sessions.count()} previous active sessions")
            previous_sessions.update(is_active=False)
            
            # Create new session
            logger.info("Creating new session")
            session = Session.objects.create(
                user=user, 
                duration=duration, 
                status='pending', 
                device_id=device_id, 
                is_active=True
            )
            logger.info(f"Session created successfully with ID: {session.id}")
            
            response_data = {'session_id': session.id}
            logger.info(f"Returning response: {response_data}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Unexpected error in StartSessionView: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)