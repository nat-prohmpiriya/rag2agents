// Sidebar state using Svelte 5 runes
const STORAGE_KEY = 'sidebar_collapsed';

let collapsed = $state(false);

// Initialize from localStorage
function initialize(): void {
	if (typeof window === 'undefined') return;

	const stored = localStorage.getItem(STORAGE_KEY);
	if (stored !== null) {
		collapsed = stored === 'true';
	}
}

// Toggle collapsed state
function toggle(): void {
	collapsed = !collapsed;
	if (typeof window !== 'undefined') {
		localStorage.setItem(STORAGE_KEY, String(collapsed));
	}
}

// Set collapsed state directly
function setCollapsed(value: boolean): void {
	collapsed = value;
	if (typeof window !== 'undefined') {
		localStorage.setItem(STORAGE_KEY, String(value));
	}
}

// Export sidebar store
export function useSidebar() {
	return {
		get collapsed() {
			return collapsed;
		},
		initialize,
		toggle,
		setCollapsed,
	};
}

// Create singleton instance
export const sidebar = useSidebar();
