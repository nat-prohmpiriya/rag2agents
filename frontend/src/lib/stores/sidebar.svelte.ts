const STORAGE_KEY = 'sidebar_collapsed';

class SidebarStore {
	collapsed = $state(false);

	initialize() {
		if (typeof window === 'undefined') return;

		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored !== null) {
			this.collapsed = stored === 'true';
		}
	}

	toggle() {
		this.collapsed = !this.collapsed;
		if (typeof window !== 'undefined') {
			localStorage.setItem(STORAGE_KEY, String(this.collapsed));
		}
	}

	setCollapsed(value: boolean) {
		this.collapsed = value;
		if (typeof window !== 'undefined') {
			localStorage.setItem(STORAGE_KEY, String(value));
		}
	}
}

export const sidebar = new SidebarStore();
