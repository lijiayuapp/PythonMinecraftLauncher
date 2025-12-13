"""
Minecraft Authentication Library

一个独立、易用的Minecraft正版认证库，适配minecraft_downloader库。
支持微软账户认证、令牌管理和玩家信息获取。

版本: 1.0.0
作者: Minecraft Downloader Team
"""

import os
import json
import time
import uuid
import requests
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# 数据类型定义
# =============================================================================

class AuthError(Exception):
    """认证错误异常"""
    pass


class TokenExpiredError(AuthError):
    """令牌过期错误"""
    pass


class NoGameLicenseError(AuthError):
    """无游戏许可证错误"""
    pass


class LoginMethod(Enum):
    """登录方法枚举"""
    MICROSOFT_DEVICE = "microsoft_device"


@dataclass
class AuthConfig:
    """认证配置类"""
    client_id: str  # 必填：Azure应用客户端ID
    cache_file: str = "minecraft_auth_cache.json"  # 令牌缓存文件
    timeout: int = 30                               # 请求超时时间
    auto_refresh: bool = True                       # 自动刷新令牌


@dataclass
class PlayerProfile:
    """玩家档案类"""
    username: str
    uuid: str
    skin_url: Optional[str] = None
    cape_url: Optional[str] = None
    is_legacy: bool = False


@dataclass
class AuthTokens:
    """认证令牌类"""
    access_token: str
    minecraft_token: str
    xbl_token: str
    xsts_token: str
    user_hash: str
    refresh_token: Optional[str] = None
    expires_at: float = 0


@dataclass
class AuthResult:
    """认证结果类"""
    success: bool
    profile: Optional[PlayerProfile] = None
    tokens: Optional[AuthTokens] = None
    error_message: Optional[str] = None
    method: LoginMethod = LoginMethod.MICROSOFT_DEVICE


# =============================================================================
# 核心认证类
# =============================================================================

class MinecraftAuthenticator:
    """
    Minecraft正版认证器
    
    提供完整的微软账户认证流程，返回适配minecraft_downloader库的认证信息。
    开发者只需传入应用客户端ID即可完成认证。
    """
    
    # Microsoft认证端点
    MICROSOFT_DEVICE_CODE_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
    MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    
    # Xbox认证端点
    XBOX_LIVE_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate"
    XSTS_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
    
    # Minecraft认证端点
    MINECRAFT_AUTH_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
    MINECRAFT_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"
    MINECRAFT_ENTITLEMENTS_URL = "https://api.minecraftservices.com/entitlements/mcstore"
    
    def __init__(self, config: AuthConfig):
        """
        初始化认证器
        
        Args:
            config: 认证配置，必须包含client_id
        """
        if not config.client_id:
            raise ValueError("client_id必须提供")
        
        self.config = config
        self._tokens: Optional[AuthTokens] = None
        self._profile: Optional[PlayerProfile] = None
        
        # 尝试从缓存加载令牌
        self._load_cached_tokens()
    
    def _load_cached_tokens(self) -> bool:
        """从缓存文件加载令牌"""
        try:
            if os.path.exists(self.config.cache_file):
                with open(self.config.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否过期
                expires_at = cache_data.get('expires_at', 0)
                if time.time() < expires_at:
                    tokens_data = cache_data.get('tokens', {})
                    self._tokens = AuthTokens(
                        access_token=tokens_data.get('access_token', ''),
                        minecraft_token=tokens_data.get('minecraft_token', ''),
                        xbl_token=tokens_data.get('xbl_token', ''),
                        xsts_token=tokens_data.get('xsts_token', ''),
                        user_hash=tokens_data.get('user_hash', ''),
                        refresh_token=tokens_data.get('refresh_token'),
                        expires_at=tokens_data.get('expires_at', 0)
                    )
                    
                    profile_data = cache_data.get('profile', {})
                    self._profile = PlayerProfile(
                        username=profile_data.get('username', ''),
                        uuid=profile_data.get('uuid', ''),
                        skin_url=profile_data.get('skin_url'),
                        cape_url=profile_data.get('cape_url'),
                        is_legacy=profile_data.get('is_legacy', False)
                    )
                    return True
        except Exception:
            pass
        
        return False
    
    def _save_tokens_to_cache(self):
        """保存令牌到缓存文件"""
        try:
            if not self._tokens or not self._profile:
                return False
                
            cache_data = {
                'tokens': {
                    'access_token': self._tokens.access_token,
                    'refresh_token': self._tokens.refresh_token,
                    'minecraft_token': self._tokens.minecraft_token,
                    'xbl_token': self._tokens.xbl_token,
                    'xsts_token': self._tokens.xsts_token,
                    'user_hash': self._tokens.user_hash,
                    'expires_at': self._tokens.expires_at
                },
                'profile': {
                    'username': self._profile.username,
                    'uuid': self._profile.uuid,
                    'skin_url': self._profile.skin_url,
                    'cape_url': self._profile.cape_url,
                    'is_legacy': self._profile.is_legacy
                },
                'saved_at': time.time()
            }
            
            os.makedirs(os.path.dirname(os.path.abspath(self.config.cache_file)), exist_ok=True)
            
            with open(self.config.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送HTTP请求"""
        kwargs.setdefault('timeout', self.config.timeout)
        try:
            response = requests.request(method, url, **kwargs)
            return response
        except requests.RequestException as e:
            raise AuthError(f"网络请求失败: {e}")
    
    def login(self) -> AuthResult:
        """
        使用微软设备代码流登录
        
        Returns:
            认证结果
        """
        try:
            # 1. 获取设备代码
            device_response = self._make_request(
                'POST',
                self.MICROSOFT_DEVICE_CODE_URL,
                data={
                    'client_id': self.config.client_id,
                    'scope': 'XboxLive.signin offline_access'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if device_response.status_code != 200:
                return AuthResult(
                    success=False,
                    error_message=f"获取设备代码失败: {device_response.status_code}"
                )
            
            device_info = device_response.json()
            
            # 显示授权信息
            result = {
                'verification_uri': device_info['verification_uri'],
                'user_code': device_info['user_code'],
                'expires_in': device_info['expires_in'],
                'interval': device_info['interval']
            }
            
            # 2. 轮询获取访问令牌
            poll_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': self.config.client_id,
                'device_code': device_info['device_code']
            }
            
            start_time = time.time()
            while time.time() - start_time < device_info['expires_in']:
                time.sleep(device_info['interval'])
                
                poll_response = self._make_request(
                    'POST',
                    self.MICROSOFT_TOKEN_URL,
                    data=poll_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if poll_response.status_code == 200:
                    token_data = poll_response.json()
                    access_token = token_data['access_token']
                    refresh_token = token_data.get('refresh_token')
                    
                    # 继续完整认证流程
                    return self._complete_auth_flow(access_token, refresh_token)
                
                error_data = poll_response.json()
                error = error_data.get('error', '')
                
                if error == 'authorization_pending':
                    continue
                elif error in ['authorization_declined', 'bad_verification_code', 'expired_token']:
                    return AuthResult(
                        success=False,
                        error_message=f"授权失败: {error}"
                    )
            
            return AuthResult(
                success=False,
                error_message="授权超时"
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=str(e)
            )
    
    def _complete_auth_flow(self, access_token: str, refresh_token: str) -> AuthResult:
        """完成认证流程"""
        try:
            # 1. Xbox Live认证
            xbl_response = self._make_request(
                'POST',
                self.XBOX_LIVE_AUTH_URL,
                json={
                    "Properties": {
                        "AuthMethod": "RPS",
                        "SiteName": "user.auth.xboxlive.com",
                        "RpsTicket": f"d={access_token}"
                    },
                    "RelyingParty": "http://auth.xboxlive.com",
                    "TokenType": "JWT"
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if xbl_response.status_code != 200:
                return AuthResult(
                    success=False,
                    error_message=f"Xbox Live认证失败: {xbl_response.status_code}"
                )
            
            xbl_data = xbl_response.json()
            xbl_token = xbl_data['Token']
            user_hash = xbl_data['DisplayClaims']['xui'][0]['uhs']
            
            # 2. XSTS认证
            xsts_response = self._make_request(
                'POST',
                self.XSTS_AUTH_URL,
                json={
                    "Properties": {
                        "SandboxId": "RETAIL",
                        "UserTokens": [xbl_token]
                    },
                    "RelyingParty": "rp://api.minecraftservices.com/",
                    "TokenType": "JWT"
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if xsts_response.status_code != 200:
                return AuthResult(
                    success=False,
                    error_message=f"XSTS认证失败: {xsts_response.status_code}"
                )
            
            xsts_data = xsts_response.json()
            xsts_token = xsts_data['Token']
            
            # 3. Minecraft认证
            mc_response = self._make_request(
                'POST',
                self.MINECRAFT_AUTH_URL,
                json={
                    "identityToken": f"XBL3.0 x={user_hash};{xsts_token}"
                }
            )
            
            if mc_response.status_code != 200:
                return AuthResult(
                    success=False,
                    error_message=f"Minecraft认证失败: {mc_response.status_code}"
                )
            
            mc_data = mc_response.json()
            minecraft_token = mc_data['access_token']
            
            # 4. 检查游戏许可证
            if not self._check_game_entitlements(minecraft_token):
                return AuthResult(
                    success=False,
                    error_message="该账号未拥有Minecraft"
                )
            
            # 5. 获取玩家档案
            profile = self._get_player_profile(minecraft_token)
            
            # 保存令牌和档案
            self._tokens = AuthTokens(
                access_token=access_token,
                minecraft_token=minecraft_token,
                xbl_token=xbl_token,
                xsts_token=xsts_token,
                user_hash=user_hash,
                refresh_token=refresh_token,
                expires_at=time.time() + 86400  # 24小时有效
            )
            
            self._profile = profile
            
            # 保存到缓存
            self._save_tokens_to_cache()
            
            return AuthResult(
                success=True,
                profile=profile,
                tokens=self._tokens,
                method=LoginMethod.MICROSOFT_DEVICE
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=str(e)
            )
    
    def _check_game_entitlements(self, minecraft_token: str) -> bool:
        """检查游戏许可证"""
        response = self._make_request(
            'GET',
            self.MINECRAFT_ENTITLEMENTS_URL,
            headers={'Authorization': f'Bearer {minecraft_token}'}
        )
        
        if response.status_code != 200:
            return False
        
        entitlements = response.json()
        
        # 检查是否拥有Minecraft
        has_minecraft = any(
            item['name'] in ['product_minecraft', 'game_minecraft'] 
            for item in entitlements.get('items', [])
        )
        
        return has_minecraft
    
    def _get_player_profile(self, minecraft_token: str) -> PlayerProfile:
        """获取玩家档案"""
        response = self._make_request(
            'GET',
            self.MINECRAFT_PROFILE_URL,
            headers={'Authorization': f'Bearer {minecraft_token}'}
        )
        
        if response.status_code != 200:
            raise AuthError(f"获取玩家档案失败: {response.status_code}")
        
        profile_data = response.json()
        
        return PlayerProfile(
            username=profile_data['name'],
            uuid=profile_data['id'],
            skin_url=profile_data.get('skins', [{}])[0].get('url') if profile_data.get('skins') else None,
            cape_url=profile_data.get('capes', [{}])[0].get('url') if profile_data.get('capes') else None,
            is_legacy=profile_data.get('legacy', False)
        )
    
    def logout(self):
        """注销并清除缓存"""
        self._tokens = None
        self._profile = None
        
        try:
            if os.path.exists(self.config.cache_file):
                os.remove(self.config.cache_file)
        except:
            pass
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        if not self._tokens or not self._profile:
            return False
        
        # 检查令牌是否过期
        if time.time() >= self._tokens.expires_at:
            if self.config.auto_refresh and self._tokens.refresh_token:
                try:
                    # 尝试刷新令牌
                    self._refresh_tokens()
                    return True
                except:
                    return False
            return False
        
        return True
    
    def _refresh_tokens(self):
        """刷新令牌"""
        if not self._tokens or not self._tokens.refresh_token:
            return False
        
        try:
            token_response = self._make_request(
                'POST',
                self.MICROSOFT_TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'client_id': self.config.client_id,
                    'refresh_token': self._tokens.refresh_token,
                    'scope': 'XboxLive.signin offline_access'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if token_response.status_code != 200:
                return False
            
            token_data = token_response.json()
            access_token = token_data['access_token']
            refresh_token = token_data.get('refresh_token', self._tokens.refresh_token)
            
            # 重新认证
            result = self._complete_auth_flow(access_token, refresh_token)
            return result.success
            
        except Exception:
            return False
    
    def get_launch_arguments(self) -> Dict[str, str]:
        """
        获取启动参数（适配minecraft_downloader库）
        
        Returns:
            启动参数字典，包含：
            - username: 玩家用户名
            - uuid: 玩家UUID
            - access_token: Minecraft访问令牌
            - user_type: 用户类型（"msa"表示微软账户）
            
        Raises:
            AuthError: 未登录时抛出
        """
        if not self.is_logged_in():
            raise AuthError("用户未登录")
        
        return {
            "username": self._profile.username,
            "uuid": self._profile.uuid,
            "access_token": self._tokens.minecraft_token,
            "user_type": "msa"
        }
    
    def get_offline_arguments(self, custom_username: str = None) -> Dict[str, str]:
        """
        获取离线启动参数（适配minecraft_downloader库）
        
        Args:
            custom_username: 自定义用户名，如果为None则使用随机名称
            
        Returns:
            离线启动参数字典
        """
        username = custom_username or f"Player_{uuid.uuid4().hex[:8]}"
        player_uuid = str(uuid.uuid4())
        
        return {
            "username": username,
            "uuid": player_uuid,
            "access_token": f"offline_token_{uuid.uuid4().hex[:16]}",
            "user_type": "mojang"
        }
    
    def get_profile(self) -> PlayerProfile:
        """
        获取当前玩家档案
        
        Returns:
            玩家档案
            
        Raises:
            AuthError: 未登录时抛出
        """
        if not self.is_logged_in():
            raise AuthError("用户未登录")
        
        return self._profile
    
    def get_tokens(self) -> AuthTokens:
        """
        获取当前认证令牌
        
        Returns:
            认证令牌
            
        Raises:
            AuthError: 未登录时抛出
        """
        if not self.is_logged_in():
            raise AuthError("用户未登录")
        
        return self._tokens
    
    def get_device_code_info(self) -> Dict[str, str]:
        """
        获取设备代码信息（用于自定义UI显示）
        
        Returns:
            设备代码信息字典，包含：
            - verification_uri: 验证网址
            - user_code: 用户代码
            - expires_in: 过期时间（秒）
            - interval: 轮询间隔（秒）
            
        Raises:
            AuthError: 获取失败时抛出
        """
        try:
            device_response = self._make_request(
                'POST',
                self.MICROSOFT_DEVICE_CODE_URL,
                data={
                    'client_id': self.config.client_id,
                    'scope': 'XboxLive.signin offline_access'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if device_response.status_code != 200:
                raise AuthError(f"获取设备代码失败: {device_response.status_code}")
            
            device_info = device_response.json()
            
            return {
                'verification_uri': device_info['verification_uri'],
                'user_code': device_info['user_code'],
                'expires_in': device_info['expires_in'],
                'interval': device_info['interval'],
                'device_code': device_info['device_code']
            }
            
        except Exception as e:
            raise AuthError(f"获取设备代码信息失败: {e}")
    
    def poll_device_auth(self, device_code: str) -> AuthResult:
        """
        轮询设备授权状态
        
        Args:
            device_code: 设备代码
            
        Returns:
            认证结果
        """
        try:
            poll_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': self.config.client_id,
                'device_code': device_code
            }
            
            poll_response = self._make_request(
                'POST',
                self.MICROSOFT_TOKEN_URL,
                data=poll_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if poll_response.status_code == 200:
                token_data = poll_response.json()
                access_token = token_data['access_token']
                refresh_token = token_data.get('refresh_token')
                
                return self._complete_auth_flow(access_token, refresh_token)
            else:
                error_data = poll_response.json()
                error = error_data.get('error', '')
                
                if error == 'authorization_pending':
                    return AuthResult(
                        success=False,
                        error_message="等待授权中..."
                    )
                else:
                    return AuthResult(
                        success=False,
                        error_message=f"授权失败: {error}"
                    )
                    
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=str(e)
            )
