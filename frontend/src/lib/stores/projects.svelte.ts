import { projectsApi, type Project, type ProjectCreate, type ProjectUpdate } from '$lib/api';

const STORAGE_KEY = 'currentProjectId';

class ProjectStore {
	projects = $state<Project[]>([]);
	currentProjectId = $state<string | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);
	initialized = $state(false);

	currentProject = $derived(
		this.currentProjectId
			? this.projects.find((p) => p.id === this.currentProjectId) ?? null
			: null
	);

	initialize() {
		if (typeof window === 'undefined') return;

		const storedId = localStorage.getItem(STORAGE_KEY);
		if (storedId) {
			this.currentProjectId = storedId;
		}
	}

	async loadProjects() {
		if (this.loading || this.initialized) return;

		this.loading = true;
		this.error = null;

		try {
			const response = await projectsApi.list(1, 100);
			this.projects = response.items;
			this.initialized = true;

			if (this.currentProjectId && !this.projects.find((p) => p.id === this.currentProjectId)) {
				this.currentProjectId = null;
				localStorage.removeItem(STORAGE_KEY);
			}
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load projects';
			this.projects = [];
		} finally {
			this.loading = false;
		}
	}

	selectProject(id: string | null) {
		this.currentProjectId = id;

		if (typeof window !== 'undefined') {
			if (id) {
				localStorage.setItem(STORAGE_KEY, id);
			} else {
				localStorage.removeItem(STORAGE_KEY);
			}
		}
	}

	async createProject(data: ProjectCreate): Promise<Project> {
		this.loading = true;
		this.error = null;

		try {
			const project = await projectsApi.create(data);
			this.projects = [...this.projects, project];
			return project;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to create project';
			throw e;
		} finally {
			this.loading = false;
		}
	}

	async updateProject(id: string, data: ProjectUpdate): Promise<Project> {
		this.loading = true;
		this.error = null;

		try {
			const updated = await projectsApi.update(id, data);
			this.projects = this.projects.map((p) => (p.id === id ? updated : p));
			return updated;
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to update project';
			throw e;
		} finally {
			this.loading = false;
		}
	}

	async deleteProject(id: string) {
		this.loading = true;
		this.error = null;

		try {
			await projectsApi.delete(id);
			this.projects = this.projects.filter((p) => p.id !== id);

			if (this.currentProjectId === id) {
				this.selectProject(null);
			}
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to delete project';
			throw e;
		} finally {
			this.loading = false;
		}
	}

	clear() {
		this.projects = [];
		this.currentProjectId = null;
		this.error = null;
		this.initialized = false;

		if (typeof window !== 'undefined') {
			localStorage.removeItem(STORAGE_KEY);
		}
	}
}

export const projectStore = new ProjectStore();
