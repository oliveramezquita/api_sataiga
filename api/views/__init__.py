from .section import SectionView, SectionViewById, TreeView
from .role import RoleView, RoleByIdView, UpdatePermissionsView
from .user import UserView, UserByIdView, RegisterView, UpdatePasswordView
from .auth import AuthView, PasswordRequestView, RestorePasswordView
from .dashboard import DashboardView
from .client import ClientView, ClientByTypeView, ClientByIdView
from .supplier import SupplierView, SupplierByIdView
from .prototype import PrototypeView, PrototypeByIdView, PrototypeByClientView, PrototypesByDataView
from .catalog import CatalogView, CatalogByIdView
from .material import MatrialView, MaterialByIdView, DownloadMaterialsView, ImagesMaterialView, MaterialBySupplierView
from .volumetry import VolumetryView, VolumetryByIdView, VolumetryUploadView
from .tax_data import TaxDataSupplierView, TaxDataClientView
from .bank_data import BankDataView
from .refresh_rate import RefreshRateView, RefreshRatesView
from .notification import NotificationsView
from .home_production import HomeProductionView, HomeProductionByIdView
from .lot import LotsView, LotView
from .explosion import ExplosionView
from .quantification import QuantificationView, QuantificationFiltersView, QuantificationByIdView
from .contact import ContactsView, ContactByIdView
from .purchase_order import PurchaseOrdersView, PurchaseOrderView, PurchaseOrderSuppliersView, PurchaseOrderMaterialsView, ProjectsView, InputRegisterView
from .inventory import InventoryView, InventoryItemView
from .inbound import InboundsView, ProjectsListView, InboundView, InboundsByMaterialView
from .company import CompaniesView, CompanyByIdView
