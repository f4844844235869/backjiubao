from sqlmodel import Field, SQLModel


class Token(SQLModel):
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenPayload(SQLModel):
    sub: str | None = Field(default=None, description="用户 ID")
    roles: list[str] = Field(default_factory=list, description="角色编码列表")
    permissions: list[str] = Field(default_factory=list, description="权限编码列表")


class NewPassword(SQLModel):
    token: str = Field(description="重置密码令牌")
    new_password: str = Field(
        min_length=8, max_length=128, description="新密码"
    )


class BackendPasswordLoginRequest(SQLModel):
    account: str = Field(min_length=1, max_length=255, description="账号或邮箱")
    password: str = Field(min_length=8, max_length=128, description="登录密码")


class BackendMobileCodeLoginRequest(SQLModel):
    mobile: str = Field(min_length=1, max_length=32, description="手机号")
    code: str = Field(min_length=4, max_length=10, description="短信验证码")


class MiniappCodeLoginRequest(SQLModel):
    code: str = Field(min_length=1, max_length=255, description="微信登录 code")
    app_id: str | None = Field(default=None, max_length=100, description="小程序 AppID")


class SwitchCurrentStoreRequest(SQLModel):
    store_id: str = Field(description="目标门店 ID")


class MiniappBindPhoneRequest(SQLModel):
    phone: str = Field(min_length=1, max_length=32, description="手机号")
    country_code: str = Field(
        default="+86", min_length=1, max_length=10, description="国家区号"
    )


LoginRequest = BackendPasswordLoginRequest
