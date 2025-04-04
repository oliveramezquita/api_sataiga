from .section import SectionView, SectionViewById, TreeView
from .role import RoleView, RoleByIdView, UpdatePermissionsView
from .user import UserView, UserByIdView, RegisterView, UpdatePasswordView
from .auth import AuthView, PasswordRequestView, RestorePasswordView
from .dashboard import DashboardView
from .client import ClientView, ClientByTypeView, ClientByIdView
from .supplier import SupplierView, SupplierByIdView
from .prototype import PrototypeView, PrototypeByIdView, PrototypeByClientView
from .catalog import CatalogView, CatalogByIdView
from .material import MatrialView, MaterialByIdView
from .volumetry import VolumetryView, VolumetryByIdView
